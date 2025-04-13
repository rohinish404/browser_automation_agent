# llm_translator.py
import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

# Configure Groq client
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    logger.warning("GROQ_API_KEY not found in environment variables.")
    # Optionally raise an error or provide a default behavior
    # raise ValueError("GROQ_API_KEY must be set")
    aclient = None # Or configure a fallback client if desired
else:
    aclient = AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_api_key
    )

SYSTEM_PROMPT = """
You are an AI agent controlling a web browser based on user commands.
Your goal is to translate the user's command into a single, executable browser action.
You are given the user's command and the current state of the browser, which includes:
- `url`: The current URL.
- `title`: The current page title.
- `elements`: A list of visible interactive elements on the page. Each element is a dictionary containing its `tag`, and potentially attributes like `text`, `id`, `name`, `placeholder`, `aria-label`, `type`, `role`, `value`.

Available actions:
1.  `navigate`: Go to a specific URL. Requires `url` parameter (e.g., {"action": "navigate", "parameters": {"url": "https://example.com"}}).
2.  `click`: Click on an element. Requires a `selector` parameter (CSS selector) (e.g., {"action": "click", "parameters": {"selector": "button#login-button"}}).
3.  `type`: Type text into an input field. Requires `selector` (CSS selector) and `text` parameters (e.g., {"action": "type", "parameters": {"selector": "input[name='username']", "text": "myuser"}}).
4.  `scroll`: Scroll the page up or down. Requires `direction` parameter ("up" or "down") (e.g., {"action": "scroll", "parameters": {"direction": "down"}}).

Based on the user command and the *provided elements list*, determine the most appropriate *single* action to perform next.

**IMPORTANT for `click` and `type` actions:**
- Analyze the `elements` list carefully to find the element that best matches the user's intent (text content, labels, placeholders, etc.).
- Construct the most robust and specific CSS selector possible for the *target element* identified in the list.
- **Prioritize using unique attributes**: id, name, aria-label, test-id (if available). Use them directly: `#element-id`, `[name="user_name"]`, `[aria-label="Search website"]`.
- If unique attributes are missing, combine tag with other attributes or text: `button:has-text('Log In')`, `input[placeholder='Enter your email']`, `a[role='menuitem']:has-text('Profile')`.
- Be precise with text matching: Use `has-text("Exact Text")`. Escape quotes within the text if necessary (e.g., `has-text(\\"User's Guide\\")`).
- If multiple similar elements exist, try to find distinguishing attributes or use positional selectors like `:first`, `:nth-child(n)`, but only if the user's command implies position (e.g., "click the first button").

**SPECIAL INSTRUCTIONS FOR GOOGLE SEARCH RESULTS:**
- Search results are usually links (`<a>` tag) often containing a heading (`<h3>` tag with the result title).
- To target the **first search result link**, a reliable selector is often `div#search a:has(h3):first-of-type`. Use this pattern if the user asks for the first result.
- If the user asks for a result by its title (e.g., "Click the link titled 'Playwright Docs'"), find the `<a>` tag containing an `<h3>` with that text. A good selector might be `a:has(h3:has-text("Playwright Docs"))`. Adapt the text precisely.

- Ensure the generated selector uniquely targets the intended element based on the provided list and common web structures. Do not invent selectors for elements not present in the list unless it's a standard browser feature (like scroll).

Respond ONLY with a single JSON object containing the fields "action" (string) and "parameters" (object).
Example Command: "Go to playwright.dev"
Example State: {"url": "https://google.com", "title": "Google", "elements": []}
Example Response: {"action": "navigate", "parameters": {"url": "https://playwright.dev"}}

Example Command: "Type 'test query' into the search bar"
Example State: {"url": "https://google.com", "title": "Google", "elements": [{"tag":"textarea", "name": "q", "aria-label": "Search"}]}
Example Response: {"action": "type", "parameters": {"selector": "textarea[name='q']", "text": "test query"}}

Example Command: "Click the login button"
Example State: {"url": "...", "title": "...", "elements": [{"tag": "button", "id": "login-btn", "text": "Log In"}]}
Example Response: {"action": "click", "parameters": {"selector": "#login-btn"}}

Example Command: "Click the first search result link"
Example State: {"url": "https://google.com/search?q=...", "title": "Search Results", "elements": [...]}
Example Response: {"action": "click", "parameters": {"selector": "div#search a:has(h3):first-of-type"}}

Example Command: "Click the result titled 'Official Python Website'"
Example State: {"url": "https://google.com/search?q=...", "title": "Search Results", "elements": [{"tag": "a", "href":"...", "text": "..."}, {"tag": "h3", "text": "Official Python Website"}, ...]}
Example Response: {"action": "click", "parameters": {"selector": "a:has(h3:has-text(\\"Official Python Website\\"))"}}

Example Command: "Scroll down"
Example State: {"url": "...", "title": "...", "elements": [...]}
Example Response: {"action": "scroll", "parameters": {"direction": "down"}}
"""

async def translate_command_to_action(command: str, state: dict) -> dict | None:
    """
    Translates a natural language command and browser state into a structured action.

    Args:
        command: The user's natural language command.
        state: The current state of the browser page (URL, title, elements).

    Returns:
        A dictionary representing the action (e.g., {"action": "click", "parameters": {"selector": "..."}})
        or None if translation fails.
    """
    if not aclient:
        logger.error("LLM client is not initialized. Cannot translate command.")
        return None

    logger.info(f"Translating command: '{command}'")
    # logger.debug(f"State received by translator: {json.dumps(state, indent=2)}") # Uncomment for deep debugging state

    action_json = None # Initialize for error handling scope
    try:
        # Prepare state for prompt, truncate elements if too long
        prompt_state = state.copy()
        max_elements_in_prompt = 25 # Limit elements sent to LLM
        if len(prompt_state.get("elements", [])) > max_elements_in_prompt:
             logger.warning(f"Truncating elements list from {len(prompt_state['elements'])} to {max_elements_in_prompt} for LLM prompt.")
             prompt_state["elements"] = prompt_state["elements"][:max_elements_in_prompt]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Command: \"{command}\"\nCurrent State: {json.dumps(prompt_state)}"}
        ]

        response = await aclient.chat.completions.create(
            model="llama3-70b-8192", # Powerful model for complex instructions
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.05, # Low temperature for deterministic output
            max_tokens=500, # Limit response size
            # Consider adding stop sequences if needed
        )

        action_json = response.choices[0].message.content
        logger.info(f"LLM Response JSON: {action_json}")
        action_data = json.loads(action_json)

        # Basic validation
        if not isinstance(action_data, dict):
             raise ValueError(f"LLM response is not a JSON object: {action_data}")
        if "action" not in action_data or not isinstance(action_data["action"], str):
             raise ValueError("LLM response missing or invalid 'action' key.")
        if "parameters" not in action_data or not isinstance(action_data["parameters"], dict):
             raise ValueError("LLM response missing or invalid 'parameters' key.")

        action_name = action_data["action"]
        params = action_data["parameters"]

        # Action-specific parameter validation
        if action_name == "navigate" and ("url" not in params or not isinstance(params.get("url"), str)):
             raise ValueError("LLM response for 'navigate' missing or invalid 'url' parameter.")
        if action_name in ["click", "type"] and ("selector" not in params or not isinstance(params.get("selector"), str)):
             raise ValueError(f"LLM response for action '{action_name}' missing or invalid 'selector' parameter.")
        if action_name == "type" and ("text" not in params or not isinstance(params.get("text"), str)):
             raise ValueError("LLM response for action 'type' missing 'text' parameter.")
        if action_name == "scroll" and ("direction" not in params or params.get("direction") not in ["up", "down"]):
             raise ValueError("LLM response for 'scroll' missing or invalid 'direction' parameter.")
        if action_name not in ["navigate", "click", "type", "scroll"]:
            raise ValueError(f"LLM proposed an unknown action: '{action_name}'")


        logger.info(f"Translation successful: Action='{action_name}', Params={params}")
        return action_data

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing LLM JSON response: {e}\nRaw Response: {action_json}")
        return None
    except Exception as e:
        # Catch OpenAI specific errors if needed, or general exceptions
        logger.error(f"Error interacting with LLM or validating response: {e}")
        return None