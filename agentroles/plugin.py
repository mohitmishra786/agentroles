"""Plugin interface for target generators.

To add a new target generator (e.g., CrewAI, LangGraph, Copilot .agent.md),
implement :class:`TargetGenerator` and register it via the ``TARGET_GENERATORS``
entry point group in your package's ``pyproject.toml``.

Example::

    # my_crewai_generator/plugin.py
    from agentroles.plugin import TargetGenerator, TargetType

    class CrewAIGenerator(TargetGenerator):
        target_type: TargetType = TargetType.CREWAI

        def generate(self, config: AgentRolesConfig, result: GenerationResult) -> None:
            # write crew_config.py
            ...

    # pyproject.toml
    [project.entry-points."agentroles.targets"]
    crewai = "my_crewai_generator.plugin:CrewAIGenerator"

The core agentroles package discovers plugins automatically. No changes to
the agentroles source code are needed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import AgentRolesConfig, TargetType


class GenerationResult:
    """Collector for per-file generation results."""

    def __init__(self) -> None:
        self.files_written: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def add_file(self, path: str) -> None:
        self.files_written.append(path)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def __repr__(self) -> str:
        return (
            f"GenerationResult(files={len(self.files_written)}, "
            f"warnings={len(self.warnings)}, errors={len(self.errors)})"
        )


class TargetGenerator(ABC):
    """Base class for target config generators.

    Subclasses implement ``generate()`` to produce tool-specific config files
    from the universal ``agentroles.yaml`` source of truth.
    """

    @property
    @abstractmethod
    def target_type(self) -> TargetType:
        ...

    @abstractmethod
    def generate(self, config: AgentRolesConfig, base_dir: Path, result: GenerationResult) -> None:
        """Generate config files for this target tool.

        Args:
            config: The validated configuration model.
            base_dir: The project root directory (paths in config relative to this).
            result: Accumulate file paths written and any warnings/errors.
        """
        ...
