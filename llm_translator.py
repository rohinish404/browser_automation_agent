import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    logger.warning("GROQ_API_KEY not found in environment variables.")
    aclient = None
else:
    aclient = AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_api_key
    )

SYSTEM_PROMPT = """
You are an AI agent controlling a web browser **at the OS level** based on user commands.
You **cannot** directly access the web page's structure (DOM). You interact by **simulating mouse clicks and keyboard input** based on visual cues described in text or seen in screenshots.

Your goal is to translate the user's command into a single, executable OS-level browser action.

You are given the user's command and the current state of the browser screen, which includes:
- `url`: The current URL (may be 'unknown - OS control').
- `title`: The current page title (may be 'unknown - OS control').
- `visible_text`: Text content extracted from the **visible part** of the screen via OCR (Optical Character Recognition). This text might be messy or incomplete.
- `screenshot_base64`: (Optional) A base64 encoded screenshot of the current screen, if a vision model is used.

Available OS-level actions:
1.  `navigate`: Go to a specific URL. Requires `url` parameter. This simulates typing into the address bar.
2.  `click`: Click on a visual element described by the user. Requires `target_description` parameter (e.g., "the 'Login' button", "the search icon", "the text input field with placeholder 'Username'"). The controller will try to find this element visually (e.g., using image matching or OCR).
3.  `type`: Type text into a field. Requires `target_description` (description of the input field) and `text` parameters. This simulates clicking the field and typing.
4.  `scroll`: Scroll the page up or down. Requires `direction` parameter ("up" or "down").
5.  `press_key`: Press a single keyboard key. Requires `key_name` parameter (e.g., "enter", "tab", "esc", "pagedown").

Based on the user command and the *provided screen state (especially visible_text or screenshot)*, determine the most appropriate *single* action to perform next.

**IMPORTANT for `click` and `type` actions:**
- Analyze the `visible_text` (and screenshot if available) to identify the visual target mentioned in the user command.
- Provide a clear, concise `target_description` for the OS controller to find (e.g., "the button labeled 'Submit'", "the search bar near the top", "the link titled 'About Us'"). Use descriptive labels, text content, or relative positions if possible. **Do NOT use CSS selectors or XPaths.**
- **After typing into a search bar or form field, you often need to press 'enter' to submit. Use the `press_key` action with `key_name: 'enter'` for this in the next step.**

Example Command: "Go to google.com"
Example State: {"url": "unknown", "title": "unknown", "visible_text": "..."}
Example Response: {"action": "navigate", "parameters": {"url": "https://google.com"}}

Example Command: "Click the 'Sign In' button"
Example State: {"url": "...", "title": "...", "visible_text": "... Sign In ..."}
Example Response: {"action": "click", "parameters": {"target_description": "Sign In button"}}

Example Command: "Type 'hello world' into the search bar"
Example State: {"url": "...", "title": "...", "visible_text": "... Search ..."}
Example Response: {"action": "type", "parameters": {"target_description": "search bar", "text": "hello world"}}

Example Command: "Search for it" (Assuming 'hello world' was just typed into the search bar)
Example State: {"url": "...", "title": "...", "visible_text": "..."}
Example Response: {"action": "press_key", "parameters": {"key_name": "enter"}}

Example Command: "Scroll down"
Example State: {"url": "...", "title": "...", "visible_text": "..."}
Example Response: {"action": "scroll", "parameters": {"direction": "down"}}

Respond ONLY with a single JSON object containing the fields "action" (string) and "parameters" (object).
"""

async def translate_command_to_action(command: str, state: dict) -> dict | None:
    """
    Translates a natural language command and OS-level browser state into a structured action.

    Args:
        command: The user's natural language command.
        state: The current state of the browser screen (URL, title, visible_text, screenshot).

    Returns:
        A dictionary representing the action (e.g., {"action": "click", "parameters": {"target_description": "..."}})
        or None if translation fails.
    """
    if not aclient:
        logger.error("LLM client is not initialized. Cannot translate command.")
        return None

    logger.info(f"Translating command for OS control: '{command}'")
    log_state = {k: v for k, v in state.items() if k != 'screenshot_base64'}
    logger.debug(f"State received by OS translator: {json.dumps(log_state, indent=2)}")

    action_json = None
    try:
        prompt_state = state.copy()
        max_text_length = 2000
        if prompt_state.get("visible_text") and len(prompt_state["visible_text"]) > max_text_length:
            logger.warning(f"Truncating visible_text from {len(prompt_state['visible_text'])} to {max_text_length} for LLM prompt.")
            prompt_state["visible_text"] = prompt_state["visible_text"][:max_text_length] + "..."

        prompt_state.pop("screenshot_base64", None)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Command: \"{command}\"\nCurrent State: {json.dumps(prompt_state)}"}
        ]

        logger.info("------ LLM Request Payload ------")
        try:
            messages_json = json.dumps(messages, indent=2)
            logger.info(f"Messages:\n{messages_json}")
        except Exception:
            logger.info(f"Messages (raw): {messages}")
        logger.info("---------------------------------")

        response = await aclient.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.05,
            max_tokens=500,
        )

        action_json = response.choices[0].message.content
        logger.info(f"LLM OS Control Response JSON: {action_json}")
        action_data = json.loads(action_json)

        if not isinstance(action_data, dict):
             raise ValueError(f"LLM response is not a JSON object: {action_data}")
        if "action" not in action_data or not isinstance(action_data["action"], str):
             raise ValueError("LLM response missing or invalid 'action' key.")
        if "parameters" not in action_data or not isinstance(action_data["parameters"], dict):
             raise ValueError("LLM response missing or invalid 'parameters' key.")

        action_name = action_data["action"]
        params = action_data["parameters"]

        if action_name == "navigate" and ("url" not in params or not isinstance(params.get("url"), str)):
             raise ValueError("LLM response for 'navigate' missing or invalid 'url' parameter.")
        if action_name in ["click", "type"] and ("target_description" not in params or not isinstance(params.get("target_description"), str)):
             raise ValueError(f"LLM response for action '{action_name}' missing or invalid 'target_description' parameter.")
        if action_name == "type" and ("text" not in params or not isinstance(params.get("text"), str)):
             raise ValueError("LLM response for action 'type' missing 'text' parameter.")
        if action_name == "scroll" and ("direction" not in params or params.get("direction") not in ["up", "down"]):
             raise ValueError("LLM response for 'scroll' missing or invalid 'direction' parameter.")
        if action_name == "press_key" and ("key_name" not in params or not isinstance(params.get("key_name"), str)):
             raise ValueError("LLM response for 'press_key' missing or invalid 'key_name' parameter.")

        if action_name not in ["navigate", "click", "type", "scroll", "press_key"]:
            raise ValueError(f"LLM proposed an unknown action: '{action_name}'")

        logger.info(f"OS Translation successful: Action='{action_name}', Params={params}")
        return action_data

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing LLM JSON response: {e}\nRaw Response: {action_json}")
        return None
    except Exception as e:
        logger.error(f"Error interacting with LLM or validating response: {e}")
        return None