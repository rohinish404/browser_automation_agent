# interaction_agent.py
import asyncio
import logging
from os_controller import OSController
from extractor import extract_data
from llm_translator import translate_command_to_action
import json # Import json

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
        self.controller.teardown() # OSController uses teardown
        self._is_setup = False
        logger.info("Interaction Agent closed.")

    def interact(self, command: str) -> dict:
        """
        Takes a natural language command, translates it, executes it via OS control,
        and returns the result.

        Args:
            command: The natural language command from the user.

        Returns:
            A dictionary containing the result of the action execution.
        """
        if not self._is_setup:
            logger.error("Agent is not set up. Please call setup() first.")
            return {"success": False, "error": "Agent not initialized"}

        logger.info(f"Received OS command: '{command}'")

        # 1. Get Current State (from OS perspective)
        try:
            current_state = self.controller.get_current_state()
            log_state = {k: v for k, v in current_state.items() if k != 'screenshot_base64'}
            # print(log_state)
            logger.debug(f"Current OS State: {json.dumps(log_state, indent=2)}") # Use json.dumps for better formatting
        except Exception as e:
            logger.error(f"Failed to get current OS state: {e}")
            return {"success": False, "error": f"Failed to get OS state: {e}"}
        
         # --- PREPARE MESSAGES (This part is usually in llm_translator, but let's do it here for logging) ---
    # This replicates the message preparation logic from llm_translator.py
    # to ensure we log the *exact* payload *before* the async call hangs.

        print("DEBUG: Preparing messages for LLM translator...")
        prompt_state = current_state.copy()
        max_text_length = 2000
        if prompt_state.get("visible_text") and len(prompt_state["visible_text"]) > max_text_length:
            prompt_state["visible_text"] = prompt_state["visible_text"][:max_text_length] + "..."
        prompt_state.pop("screenshot_base64", None)

        # Get the system prompt content from llm_translator
        from llm_translator import SYSTEM_PROMPT

        messages_payload = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Command: \"{command}\"\nCurrent State: {json.dumps(prompt_state)}"}
        ]

        # --- Log the Prepared Payload ---
        logger.info("------ LLM Request Payload (Prepared in Agent) ------")
        try:
            messages_json = json.dumps(messages_payload, indent=2)
            logger.info(f"Messages:\n{messages_json}")
            print("DEBUG: Successfully prepared and logged messages payload.")
        except Exception as log_err:
            logger.error(f"Failed to serialize messages for logging: {log_err}")
            print(f"DEBUG: ERROR during logging preparation: {log_err}")
        logger.info("----------------------------------------------------")


        # 2. Translate Command to OS Action
        # Need to run the async translator in the current event loop if main is async,
        # or run it synchronously if the interact method itself is not async.
        # Running synchronously for simplicity in this example:
        print("DEBUG: About to call LLM translator...")
        try:
            # Check if an event loop is running, if not, start one temporarily
            loop = asyncio.get_event_loop()
            print(f"DEBUG: Event loop running? {loop.is_running()}")
            if loop.is_running():
                 # If called from an async context (like main), create a task
                 # This might require making interact() async itself
                 # For now, assume interact is called synchronously or handle appropriately
                 # action_plan = await asyncio.create_task(translate_command_to_action(command, current_state)) # If interact is async
                 action_plan = asyncio.run_coroutine_threadsafe(
                    translate_command_to_action(command, current_state),
                    loop
                 ).result(timeout=180) # If interact is sync but called from thread with loop
                 print("DEBUG: Translator finished (via run_coroutine_threadsafe).")
            else:
                 # If no loop running, run it synchronously
                 action_plan = asyncio.run(translate_command_to_action(command, current_state))
                 print("DEBUG: Translator finished (via asyncio.run).")
        except asyncio.TimeoutError: # Catch the timeout
            print("DEBUG: LLM Translator timed out!") # <--- ADD THIS
            logger.error("LLM translation timed out.")
            action_plan = None
        except RuntimeError: # Handle cases where no event loop exists or is already closed
            print(f"DEBUG: Runtime error during translation call: {e}")
            try:
                action_plan = asyncio.run(translate_command_to_action(command, current_state))
                print("DEBUG: Translator finished (via fallback asyncio.run).")
            except Exception as final_e:
              print(f"DEBUG: Fallback translation call failed: {final_e}") # <--- ADD THIS
              logger.error(f"LLM translation failed even in fallback: {final_e}")
              action_plan = None
        except Exception as e:
            print(f"DEBUG: General error during translation call: {e}") # <--- ADD THIS
            logger.error(f"LLM translation failed: {e}")
            action_plan = None

        print("DEBUG: LLM translator call completed (or failed).")
        if not action_plan:
            logger.error("Failed to translate command to OS action plan.")
            return {"success": False, "error": "LLM OS translation failed"}

        action_name = action_plan.get("action")
        params = action_plan.get("parameters", {})
        logger.info(f"Executing OS action: {action_name} with params: {params}")

        # 3. Execute OS Action using OSController
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
            # +++ ADDED CASE +++
            elif action_name == "press_key":
                result = self.controller.press_key(**params)
            # +++ END ADDED CASE +++
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

        # 1. Get Current State (includes visible_text and maybe screenshot)
        try:
            current_state = self.controller.get_current_state()
        except Exception as e:
            logger.error(f"Failed to get current OS state for extraction: {e}")
            return {"error": f"Failed to get OS state for extraction: {e}"}

        # 2. Call the extractor function
        try:
            extracted_data = await extract_data(query, current_state)
            logger.info(f"Extraction result: {extracted_data}")
            return extracted_data
        except Exception as e:
            logger.error(f"Error during data extraction: {e}")
            return {"error": f"Data extraction failed: {e}"}