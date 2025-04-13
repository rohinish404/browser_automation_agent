# llm_translator.py
import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

aclient = AsyncOpenAI(base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are an AI agent controlling a web browser based on user commands.
Your goal is to translate the user's command into a single, executable browser action.
You are given the user's command and the current state of the browser, which includes:
- `url`: The current URL.
- `title`: The current page title.
- `elements`: A list of visible interactive elements on the page. Each element is a dictionary containing its `tag`, and potentially attributes like `text`, `id`, `name`, `placeholder`, `aria-label`, `type`, `role`, `value`.

Available actions:
1.  `navigate`: Go to a specific URL. Requires `url` parameter.
2.  `click`: Click on an element. Requires a `selector` parameter (CSS selector).
3.  `type`: Type text into an input field. Requires `selector` (CSS selector) and `text` parameters.
4.  `scroll`: Scroll the page up or down. Requires `direction` parameter ("up" or "down").


Based on the user command and the *provided elements list*, determine the most appropriate *single* action to perform next.

**IMPORTANT for `click` and `type` actions:**
- Analyze the `elements` list to find the element that best matches the user's command.
- Construct the best possible CSS selector for the *target element* identified in the list.
- **Prioritize using unique attributes**: id, name, aria-label, placeholder.
- If unique attributes are missing, combine tag with text: `button:has-text('Log In')`.

**SPECIAL INSTRUCTIONS FOR GOOGLE SEARCH RESULTS:**
- Search results are usually links (`<a>` tag) containing a heading (`<h3>` tag with the result title).
- To target the **first search result link**, a reliable selector is often `div#search a:has(h3):first-of-type`. Use this pattern if the user asks for the first result.
- If the user asks for a result by its title (e.g., "Click the link titled 'Playwright Docs'"), find the `<a>` tag containing an `<h3>` with that text. A good selector might be `a:has(h3:has-text("Playwright Docs"))`.

- Ensure the generated selector uniquely targets the intended element based on the provided list.

Respond ONLY with a single JSON object... (Keep Format and remaining examples) ...

Example Command: "Click the first search result link"
Example State: {"url": "https://google.com/search?q=...", "title": "Search Results", "elements": [...]}
Example Response: {"action": "click", "parameters": {"selector": "div#search a:has(h3):first-of-type"}}

Example Command: "Click the result titled 'Official Python Website'"
Example State: {"url": "https://google.com/search?q=...", "title": "Search Results", "elements": [{"tag": "a", "href":"...", "text": "..."}, {"tag": "h3", "text": "Official Python Website"}, ...]}
Example Response: {"action": "click", "parameters": {"selector": "a:has(h3:has-text(\\"Official Python Website\\"))"}}
"""

async def translate_command_to_action(command: str, state: dict) -> dict | None:
    print(f"Translating command: '{command}'") # State can be large, print selectively
    # print(f"State received by translator: {json.dumps(state, indent=2)}") # Uncomment for debugging state
    try:
        # Prepare state for prompt, maybe truncate elements if too long
        prompt_state = state.copy()
        if len(prompt_state.get("elements", [])) > 25: # Limit elements in prompt
             print(f"Truncating elements list from {len(prompt_state['elements'])} to 25 for prompt.")
             prompt_state["elements"] = prompt_state["elements"][:25]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Command: \"{command}\"\nCurrent State: {json.dumps(prompt_state)}"}
        ]

        response = await aclient.chat.completions.create(
            model="llama3-70b-8192", # Consider gpt-4o if mini struggles
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1, # Even lower temperature
        )

        action_json = response.choices[0].message.content
        print(f"LLM Response: {action_json}")
        action_data = json.loads(action_json)

        # Basic validation
        if "action" not in action_data or "parameters" not in action_data:
             raise ValueError("LLM response missing 'action' or 'parameters' key.")
        if action_name := action_data.get("action"):
             if action_name in ["click", "type"] and "selector" not in action_data.get("parameters", {}):
                 raise ValueError(f"LLM response for action '{action_name}' missing 'selector' parameter.")
             if action_name == "type" and "text" not in action_data.get("parameters", {}):
                 raise ValueError("LLM response for action 'type' missing 'text' parameter.")
             # Add more validation as needed

        return action_data
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM JSON response: {e}\nResponse: {action_json}")
        return None
    except Exception as e:
        print(f"Error interacting with LLM: {e}")
        return None