# __init__.py
# Make the agent easily importable
from .interaction_agent import InteractionAgent
from .browser_controller import AsyncBrowserController
from .llm_translator import translate_command_to_action

# Optional: Define package-level metadata if needed
__version__ = "0.1.0"