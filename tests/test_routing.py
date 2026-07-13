from __future__ import annotations

from agentroles.models import (
    AgentRolesConfig,
    EscalationSignal,
    RoleConfig,
    RoutingConfig,
    RoutingMode,
)
from agentroles.routing import (
    EscalationRouter,
    StepOutcome,
    TaskState,
    _CacheAwarenessEstimator,
)


def _make_static_config():
    role = RoleConfig(
        primary="anthropic/claude-haiku-4-5",
        fallback=["openai/gpt-4o-mini", "deepseek/deepseek-coder"],
    )
    return AgentRolesConfig(
        roles={"implementer": role},
        routing=RoutingConfig(mode=RoutingMode.STATIC),
    )


def _make_dynamic_config():
    role = RoleConfig(
        primary="anthropic/claude-haiku-4-5",
        fallback=["openai/gpt-4o-mini", "deepseek/deepseek-coder"],
    )
    from agentroles.models import DynamicRoutingConfig

    return AgentRolesConfig(
        roles={"implementer": role},
        routing=RoutingConfig(
            mode=RoutingMode.DYNAMIC,
            dynamic=DynamicRoutingConfig(
                enabled=True,
                escalate_on=[
                    EscalationSignal.TEST_FAILURE,
                    EscalationSignal.LOW_CONFIDENCE,
                    EscalationSignal.PLAN_REVISION,
                ],
                cache_aware=True,
            ),
        ),
    )


class TestEscalationRouter:
    def test_static_mode_always_returns_primary(self):
        config = _make_static_config()
        router = EscalationRouter(config)
        state = TaskState(current_role="implementer")

        decision = router.route("implementer", state, StepOutcome.SUCCESS)
        assert decision.model == "anthropic/claude-haiku-4-5"
        assert not decision.escalated

        decision = router.route("implementer", state, StepOutcome.TEST_FAILURE)
        assert decision.model == "anthropic/claude-haiku-4-5"
        assert not decision.escalated

    def test_dynamic_mode_no_signal_returns_primary(self):
        config = _make_dynamic_config()
        router = EscalationRouter(config)
        state = TaskState(current_role="implementer")

        decision = router.route("implementer", state, StepOutcome.SUCCESS)
        assert decision.model == "anthropic/claude-haiku-4-5"
        assert not decision.escalated

    def test_dynamic_mode_escalates_on_test_failure(self):
        config = _make_dynamic_config()
        router = EscalationRouter(config)
        state = TaskState(current_role="implementer", last_model_used="anthropic/claude-haiku-4-5")

        decision = router.route("implementer", state, StepOutcome.TEST_FAILURE)
        assert decision.escalated
        assert decision.model.startswith("openai")
        assert decision.escalation_reason == "test_failure"

    def test_dynamic_mode_escalates_on_low_confidence(self):
        from agentroles.models import DynamicRoutingConfig

        role = RoleConfig(
            primary="anthropic/claude-haiku-4-5",
            fallback=["openai/gpt-4o-mini"],
        )
        config = AgentRolesConfig(
            roles={"implementer": role},
            routing=RoutingConfig(
                mode=RoutingMode.DYNAMIC,
                dynamic=DynamicRoutingConfig(
                    enabled=True,
                    escalate_on=[EscalationSignal.LOW_CONFIDENCE],
                    cache_aware=False,
                ),
            ),
        )
        router = EscalationRouter(config)
        state = TaskState(current_role="implementer", last_model_used="anthropic/claude-haiku-4-5")

        decision = router.route("implementer", state, StepOutcome.LOW_CONFIDENCE)
        assert decision.escalated
        assert decision.model.startswith("openai")

    def test_dynamic_mode_escalates_on_plan_revision(self):
        config = _make_dynamic_config()
        router = EscalationRouter(config)
        state = TaskState(current_role="implementer", last_model_used="anthropic/claude-haiku-4-5")

        decision = router.route("implementer", state, StepOutcome.PLAN_REVISION)
        assert decision.escalated
        assert decision.model.startswith("openai")

    def test_eskalation_exhausts_fallbacks(self):
        config = _make_dynamic_config()
        router = EscalationRouter(config)
        state = TaskState(current_role="implementer", last_model_used="anthropic/claude-haiku-4-5")

        decision = router.route("implementer", state, StepOutcome.TEST_FAILURE)
        assert decision.escalated
        assert decision.model.startswith("openai")

        decision = router.route("implementer", state, StepOutcome.TEST_FAILURE)
        assert decision.escalated
        assert decision.model.startswith("deepseek")

        decision = router.route("implementer", state, StepOutcome.TEST_FAILURE)
        assert not decision.escalated

    def test_escalation_respects_max_limit(self):
        config = _make_dynamic_config()
        router = EscalationRouter(config)
        state = TaskState(current_role="implementer", max_escalations=1, last_model_used="anthropic/claude-haiku-4-5")

        decision = router.route("implementer", state, StepOutcome.TEST_FAILURE)
        assert decision.escalated

        decision = router.route("implementer", state, StepOutcome.TEST_FAILURE)
        assert not decision.escalated

    def test_task_state_records_escalation(self):
        config = _make_dynamic_config()
        router = EscalationRouter(config)
        state = TaskState(current_role="implementer", last_model_used="anthropic/claude-haiku-4-5")

        router.route("implementer", state, StepOutcome.TEST_FAILURE)
        assert len(state.history) == 1
        assert state.history[0].signal == StepOutcome.TEST_FAILURE
        assert state.history[0].from_model == "anthropic/claude-haiku-4-5"

    def test_unknown_role_returns_empty(self):
        config = _make_static_config()
        router = EscalationRouter(config)
        state = TaskState()

        decision = router.route("nonexistent", state)
        assert decision.model == ""
        assert decision.role == "nonexistent"


class TestCacheAwareness:
    def test_detects_provider_switch(self):
        assert _CacheAwarenessEstimator.would_cause_cache_miss(
            "anthropic/claude-haiku-4-5", "openai/gpt-4o-mini"
        )
        assert not _CacheAwarenessEstimator.would_cause_cache_miss(
            "anthropic/claude-haiku-4-5", "anthropic/claude-sonnet-5"
        )
        assert not _CacheAwarenessEstimator.would_cause_cache_miss("", "openai/gpt-4o-mini")

    def test_signal_severity_ordering(self):
        assert _CacheAwarenessEstimator.signal_severity(StepOutcome.SUCCESS) == 0
        assert _CacheAwarenessEstimator.signal_severity(StepOutcome.LOW_CONFIDENCE) == 1
        assert _CacheAwarenessEstimator.signal_severity(StepOutcome.TEST_FAILURE) == 2
        assert _CacheAwarenessEstimator.signal_severity(StepOutcome.PLAN_REVISION) == 3

    def test_cache_aware_suppresses_low_confidence_escalation_across_providers(self):
        from agentroles.models import DynamicRoutingConfig

        role = RoleConfig(
            primary="anthropic/claude-haiku-4-5",
            fallback=["openai/gpt-4o-mini"],
        )
        config = AgentRolesConfig(
            roles={"implementer": role},
            routing=RoutingConfig(
                mode=RoutingMode.DYNAMIC,
                dynamic=DynamicRoutingConfig(
                    enabled=True,
                    escalate_on=[EscalationSignal.LOW_CONFIDENCE],
                    cache_aware=True,
                ),
            ),
        )
        router = EscalationRouter(config)
        state = TaskState(current_role="implementer", last_model_used="anthropic/claude-haiku-4-5")

        decision = router.route("implementer", state, StepOutcome.LOW_CONFIDENCE)
        assert decision.cache_miss_suppressed
        assert not decision.escalated
        assert decision.model == "anthropic/claude-haiku-4-5"

    def test_cache_aware_does_not_suppress_high_severity(self):
        from agentroles.models import DynamicRoutingConfig

        role = RoleConfig(
            primary="anthropic/claude-haiku-4-5",
            fallback=["openai/gpt-4o-mini"],
        )
        config = AgentRolesConfig(
            roles={"implementer": role},
            routing=RoutingConfig(
                mode=RoutingMode.DYNAMIC,
                dynamic=DynamicRoutingConfig(
                    enabled=True,
                    escalate_on=[EscalationSignal.TEST_FAILURE],
                    cache_aware=True,
                ),
            ),
        )
        router = EscalationRouter(config)
        state = TaskState(current_role="implementer", last_model_used="anthropic/claude-haiku-4-5")

        decision = router.route("implementer", state, StepOutcome.TEST_FAILURE)
        assert decision.escalated
        assert not decision.cache_miss_suppressed
        assert decision.model.startswith("openai")
