import asyncio
import logging
from os_controller import OSController
from extractor import extract_data
from llm_translator import translate_command_to_action
import json 

logger = logging.getLogger(__name__)

class InteractionAgent:
    """
    An agent that interacts with a web browser based on natural language commands.
    It uses an LLM to translate commands into actions and **an OS controller**
    to execute them via GUI automation. It can also extract structured data.
    """
    def __init__(self, proxy_config: str | None = None, extension_paths: list[str] | None = None):
        self.controller = OSController()
        self._is_setup = False
        self._proxy_config = proxy_config
        self._extension_paths = extension_paths
        self._loop = asyncio.get_event_loop()

    def setup(self, initial_url: str = "about:blank"):
        """Initializes the OS controller and launches the native browser."""
        if self._is_setup:
            logger.warning("Agent already set up.")
            return
        logger.info("Setting up Interaction Agent with OS Controller...")
        result = self.controller.setup(
            url=initial_url,
            proxy_config=self._proxy_config,
            extension_paths=self._extension_paths
        )
        if result["success"]:
            self._is_setup = True
            logger.info("Interaction Agent setup complete.")
        else:
            logger.error(f"Agent setup failed: {result.get('error')}")
            raise RuntimeError(f"Failed to set up OS Controller: {result.get('error')}")


    def close(self):
        """Closes the browser controller."""
        if not self._is_setup:
            logger.warning("Agent not set up, cannot close.")
            return
        logger.info("Closing Interaction Agent (OS Controller)...")
        self.controller.teardown()
        self._is_setup = False
        logger.info("Interaction Agent closed.")

    async def interact(self, command: str) -> dict:
        """
        Takes a natural language command, translates it, executes it via OS control,
        and returns the result. Now ASYNCHRONOUS.

        Args:
            command: The natural language command from the user.

        Returns:
            A dictionary containing the result of the action execution.
        """
        if not self._is_setup:
            logger.error("Agent is not set up. Please call setup() first.")
            return {"success": False, "error": "Agent not initialized"}

        logger.info(f"Received OS command: '{command}'")
        try:
            current_state = self.controller.get_current_state()
            log_state = {k: v for k, v in current_state.items() if k != 'screenshot_base64'}
            logger.debug(f"Current OS State: {json.dumps(log_state, indent=2)}")
        except Exception as e:
            logger.error(f"Failed to get current OS state: {e}")
            return {"success": False, "error": f"Failed to get OS state: {e}"}

        prompt_state = current_state.copy()
        max_text_length = 2000
        if prompt_state.get("visible_text") and len(prompt_state["visible_text"]) > max_text_length:
            prompt_state["visible_text"] = prompt_state["visible_text"][:max_text_length] + "..."
        prompt_state.pop("screenshot_base64", None)

        from llm_translator import SYSTEM_PROMPT

        messages_payload = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Command: \"{command}\"\nCurrent State: {json.dumps(prompt_state)}"}
        ]

        logger.info("------ LLM Request Payload (Prepared in Agent) ------")
        try:
            messages_json = json.dumps(messages_payload, indent=2)
            logger.info(f"Messages:\n{messages_json}")
        except Exception as log_err:
            logger.error(f"Failed to serialize messages for logging: {log_err}")
        logger.info("----------------------------------------------------")


        action_plan = None
        try:
            action_plan = await asyncio.wait_for(
                translate_command_to_action(command, current_state),
                timeout=180.0 
            )

        except asyncio.TimeoutError:
            logger.error("LLM translation timed out after 180 seconds.")
            action_plan = None
        except Exception as e:
            logger.error(f"LLM translation failed: {e}")
            action_plan = None


        if not action_plan:
            logger.error("Failed to translate command to OS action plan.")
            return {"success": False, "error": "LLM OS translation failed"}

        action_name = action_plan.get("action")
        params = action_plan.get("parameters", {})
        logger.info(f"Executing OS action: {action_name} with params: {params}")

        result = None
        try:
            if action_name == "navigate":
                result = self.controller.navigate(**params)
            elif action_name == "click":
                result = self.controller.click(target_description=params.get("target_description", "unknown target"))
            elif action_name == "type":
                result = self.controller.type(text=params.get("text", ""), target_description=params.get("target_description", "unknown target"))
            elif action_name == "scroll":
                result = self.controller.scroll(**params)
            elif action_name == "press_key":
                result = self.controller.press_key(**params)
            else:
                logger.error(f"Unknown action received from translator: {action_name}")
                result = {"success": False, "error": f"Unknown action: {action_name}"}

        except Exception as e:
            logger.error(f"Error executing OS action '{action_name}' with params {params}: {e}")
            result = {"success": False, "error": f"Execution failed for OS action {action_name}: {e}"}

        logger.info(f"OS Action result: {result}")
        return result

    async def extract(self, query: str) -> dict:
        """
        Extracts structured data from the current screen content based on a query.

        Args:
            query: Natural language query specifying what data to extract.

        Returns:
            A dictionary containing the extracted data or an error message.
        """
        if not self._is_setup:
            logger.error("Agent is not set up. Please call setup() first.")
            return {"error": "Agent not initialized"}

        logger.info(f"Received extraction query: '{query}'")

        try:
            current_state = self.controller.get_current_state()
        except Exception as e:
            logger.error(f"Failed to get current OS state for extraction: {e}")
            return {"error": f"Failed to get OS state for extraction: {e}"}

        try:
            extracted_data = await extract_data(query, current_state)
            logger.info(f"Extraction result: {extracted_data}")
            return extracted_data
        except Exception as e:
            logger.error(f"Error during data extraction: {e}")
            return {"error": f"Data extraction failed: {e}"}