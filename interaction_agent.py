# interaction_agent.py
import asyncio
import logging

from browser_controller import AsyncBrowserController

from llm_translator import translate_command_to_action

logger = logging.getLogger(__name__)

class InteractionAgent:
    """
    An agent that interacts with a web browser based on natural language commands.
    It uses an LLM to translate commands into actions and a browser controller
    to execute them.
    """
    def __init__(self):
        self.controller = AsyncBrowserController()
        self._is_setup = False

    async def setup(self, headless=False):
        """Initializes the browser controller."""
        if self._is_setup:
            logger.warning("Agent already set up.")
            return
        logger.info("Setting up Interaction Agent...")
        await self.controller.setup(headless=headless)
        self._is_setup = True
        logger.info("Interaction Agent setup complete.")

    async def close(self):
        """Closes the browser controller."""
        if not self._is_setup:
            logger.warning("Agent not set up, cannot close.")
            return
        logger.info("Closing Interaction Agent...")
        await self.controller.teardown()
        self._is_setup = False
        logger.info("Interaction Agent closed.")

    async def interact(self, command: str) -> dict:
        """
        Takes a natural language command, translates it, executes it,
        and returns the result.

        Args:
            command: The natural language command from the user.

        Returns:
            A dictionary containing the result of the action execution,
            including 'success' status and potentially other info (like URL or error message).
            Returns a failure dict if translation or execution fails.
        """
        if not self._is_setup:
            logger.error("Agent is not set up. Please call setup() first.")
            return {"success": False, "error": "Agent not initialized"}

        logger.info(f"Received command: '{command}'")

        # 1. Get Current State
        try:
            current_state = await self.controller.get_current_state()
            # Avoid printing huge state logs by default
            # logger.debug(f"Current State: {current_state}")
            if current_state.get("url") == "N/A - Page Closed":
                 logger.error("Browser page seems to be closed unexpectedly.")
                 return {"success": False, "error": "Browser page is closed"}
        except Exception as e:
            logger.error(f"Failed to get current browser state: {e}")
            return {"success": False, "error": f"Failed to get browser state: {e}"}

        # 2. Translate Command to Action
        action_plan = await translate_command_to_action(command, current_state)

        if not action_plan:
            logger.error("Failed to translate command to action plan.")
            return {"success": False, "error": "LLM translation failed"}

        action_name = action_plan.get("action")
        params = action_plan.get("parameters", {})
        logger.info(f"Executing action: {action_name} with params: {params}")

        # 3. Execute Action
        result = None
        try:
            if action_name == "navigate":
                result = await self.controller.navigate(**params)
            elif action_name == "click":
                result = await self.controller.click(**params)
            elif action_name == "type":
                result = await self.controller.type(**params)
            elif action_name == "scroll":
                result = await self.controller.scroll(**params)
            else:
                # This case should ideally be caught by translator validation
                logger.error(f"Unknown action received from translator: {action_name}")
                result = {"success": False, "error": f"Unknown action: {action_name}"}

        except Exception as e:
            logger.error(f"Error executing action '{action_name}' with params {params}: {e}")
            result = {"success": False, "error": f"Execution failed for action {action_name}: {e}"}

        logger.info(f"Action result: {result}")
        return result