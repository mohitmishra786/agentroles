"""Target generators for emitting tool-specific config files from agentroles.yaml."""

from __future__ import annotations

from .aider import AiderGenerator
from .autogen import AutoGenGenerator
from .avante_nvim import AvanteNvimGenerator
from .bitrouter import BitRouterGenerator
from .claude_code import ClaudeCodeGenerator
from .cline import ClineGenerator
from .codecompanion_nvim import CodeCompanionNvimGenerator
from .codex_cli import CodexCLIGenerator
from .cody import CodyGenerator
from .continue_ import ContinueGenerator
from .crewai import CrewAIGenerator
from .crush import CrushGenerator
from .ellama import EllamaGenerator
from .factory import FactoryGenerator
from .gemini_cli import GeminiCLIGenerator
from .goose import GooseGenerator
from .gptel import GptelGenerator
from .infermux import InferMuxGenerator
from .kilocode import KiloCodeGenerator
from .langgraph import LangGraphGenerator
from .litellm import LiteLLMGenerator
from .manifest import ManifestGenerator
from .metagpt import MetaGPTGenerator
from .opencode import OpenCodeGenerator
from .openhands import OpenHandsGenerator
from .openinterpreter import OpenInterpreterGenerator
from .pearai import PearAIGenerator
from .portkey import PortkeyGenerator
from .qodo import QodoGenerator
from .qwen_code import QwenCodeGenerator
from .zed_ai import ZedAIGenerator

__all__ = [
    "AiderGenerator",
    "AutoGenGenerator",
    "AvanteNvimGenerator",
    "BitRouterGenerator",
    "ClaudeCodeGenerator",
    "ClineGenerator",
    "CodeCompanionNvimGenerator",
    "CodexCLIGenerator",
    "CodyGenerator",
    "ContinueGenerator",
    "CrewAIGenerator",
    "CrushGenerator",
    "EllamaGenerator",
    "FactoryGenerator",
    "GeminiCLIGenerator",
    "GooseGenerator",
    "GptelGenerator",
    "InferMuxGenerator",
    "KiloCodeGenerator",
    "LangGraphGenerator",
    "LiteLLMGenerator",
    "ManifestGenerator",
    "MetaGPTGenerator",
    "OpenCodeGenerator",
    "OpenHandsGenerator",
    "OpenInterpreterGenerator",
    "PearAIGenerator",
    "PortkeyGenerator",
    "QodoGenerator",
    "QwenCodeGenerator",
    "ZedAIGenerator",
]
