"""Dynamic escalation routing runtime.

This component is opt-in and only activates when routing.mode == "dynamic"
and routing.dynamic.enabled == true in agentroles.yaml. When disabled, this
module degrades to a no-op passthrough that always returns the static-primary
model for each role.

Design principles (following Devin Fusion and ACRouter research):
- Escalate on concrete signals only (test_failure, low_confidence, plan_revision),
  never on an upfront difficulty classification.
- Cache-aware mode: suppress escalation when the expected cache-miss cost
  exceeds the benefit of switching to a stronger model.
- Degrade gracefully: if dynamic routing is disabled, behave identically to
  static mode with zero overhead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .models import (
    AgentRolesConfig,
    EscalationSignal,
    RoleConfig,
    RoutingMode,
)


class StepOutcome(str, Enum):
    SUCCESS = "success"
    TEST_FAILURE = "test_failure"
    LOW_CONFIDENCE = "low_confidence"
    PLAN_REVISION = "plan_revision"


@dataclass
class TaskState:
    current_role: str = ""
    last_model_used: str = ""
    escalation_count: int = 0
    max_escalations: int = 3
    history: list[EscalationRecord] = field(default_factory=list)

    @property
    def last_used_provider(self) -> str:
        if "/" in self.last_model_used:
            return self.last_model_used.split("/", 1)[0]
        return ""

    def record_escalation(
        self, from_role: str, from_model: str, to_model: str, signal: StepOutcome
    ) -> None:
        self.history.append(
            EscalationRecord(
                from_role=from_role,
                from_model=from_model,
                to_model=to_model,
                signal=signal,
            )
        )

    def has_escalation_signal(
        self, outcome: StepOutcome, signals: list[EscalationSignal]
    ) -> bool:
        signal_map = {
            StepOutcome.TEST_FAILURE: EscalationSignal.TEST_FAILURE,
            StepOutcome.LOW_CONFIDENCE: EscalationSignal.LOW_CONFIDENCE,
            StepOutcome.PLAN_REVISION: EscalationSignal.PLAN_REVISION,
        }
        return signal_map.get(outcome) in signals


@dataclass
class EscalationRecord:
    from_role: str
    from_model: str
    to_model: str
    signal: StepOutcome


@dataclass
class RoutingDecision:
    model: str
    role: str
    escalated: bool = False
    escalation_reason: str = ""
    cache_miss_suppressed: bool = False

    @property
    def provider(self) -> str:
        if "/" in self.model:
            return self.model.split("/", 1)[0]
        return ""


class _CacheAwarenessEstimator:
    """Heuristic estimator for whether a model switch will cause a cache miss.

    This is deliberately simple: it compares providers. Switching providers
    almost always invalidates the KV-cache on both sides, so we only suppress
    escalation when the signal severity is low and the provider would change.
    """

    @staticmethod
    def would_cause_cache_miss(current_model: str, candidate_model: str) -> bool:
        if not current_model or not candidate_model:
            return False
        current_provider = current_model.split("/", 1)[0]
        candidate_provider = candidate_model.split("/", 1)[0]
        return current_provider != candidate_provider

    @staticmethod
    def signal_severity(signal: StepOutcome) -> int:
        severities = {
            StepOutcome.SUCCESS: 0,
            StepOutcome.LOW_CONFIDENCE: 1,
            StepOutcome.TEST_FAILURE: 2,
            StepOutcome.PLAN_REVISION: 3,
        }
        return severities.get(signal, 0)


class EscalationRouter:
    """Routes to the appropriate model for a role/step, with opt-in escalation.

    Usage::

        router = EscalationRouter(config)
        decision = router.route("implementer", task_state, last_outcome)
        # call_llm(decision.model, tags={"role": decision.role})
    """

    def __init__(self, config: AgentRolesConfig) -> None:
        self._config = config
        self._routing = config.routing
        self._roles = config.roles
        self._cache_estimator = _CacheAwarenessEstimator()

    @property
    def is_dynamic_enabled(self) -> bool:
        return (
            self._routing.mode == RoutingMode.DYNAMIC and self._routing.dynamic.enabled
        )

    def route(
        self,
        role: str,
        task_state: TaskState,
        last_outcome: StepOutcome = StepOutcome.SUCCESS,
    ) -> RoutingDecision:
        role_config = self._roles.get(role)
        if not role_config:
            return RoutingDecision(model="", role=role)

        if not self.is_dynamic_enabled:
            return self._static_route(role, role_config)

        return self._dynamic_route(role, role_config, task_state, last_outcome)

    def _static_route(self, role: str, role_config: RoleConfig) -> RoutingDecision:
        return RoutingDecision(model=role_config.primary, role=role)

    def _dynamic_route(
        self,
        role: str,
        role_config: RoleConfig,
        task_state: TaskState,
        last_outcome: StepOutcome,
    ) -> RoutingDecision:
        decision = RoutingDecision(model=role_config.primary, role=role)

        escalate_signals = self._routing.dynamic.escalate_on
        should_escalate = task_state.has_escalation_signal(
            last_outcome, escalate_signals
        )

        if not should_escalate:
            task_state.last_model_used = decision.model
            return decision

        if task_state.escalation_count >= task_state.max_escalations:
            task_state.last_model_used = decision.model
            return decision

        fallback = self._pick_fallback(role_config, task_state.escalation_count)
        if not fallback:
            task_state.last_model_used = decision.model
            return decision

        if self._routing.dynamic.cache_aware:
            severity = _CacheAwarenessEstimator.signal_severity(last_outcome)
            if severity <= 1 and _CacheAwarenessEstimator.would_cause_cache_miss(
                task_state.last_model_used, fallback
            ):
                decision.cache_miss_suppressed = True
                task_state.last_model_used = role_config.primary
                return decision

        decision.escalated = True
        decision.escalation_reason = last_outcome.value
        decision.model = fallback
        task_state.record_escalation(role, role_config.primary, fallback, last_outcome)
        task_state.escalation_count += 1
        task_state.last_model_used = fallback

        return decision

    def _pick_fallback(self, role_config: RoleConfig, escalation_index: int) -> str:
        if escalation_index < len(role_config.fallback):
            return role_config.fallback[escalation_index]
        return ""
