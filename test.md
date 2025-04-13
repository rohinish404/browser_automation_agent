## Test case 1: Basic Google Search

1.  **Command:** `Go to google.com`
    *   **Expected Action:** `navigate` with `url="https://google.com"`
    *   **Expected Result:** Browser navigates to Google homepage. Success=True.

2.  **Command:** `Type 'Playwright testing framework' into the search bar`
    *   **Expected Action:** `type` with a selector targeting the search input (e.g., `textarea[name='q']`, `[aria-label="Search"]`) and `text="Playwright testing framework"`
    *   **Expected Result:** Text is entered into the search field. Success=True.

3.  **Command:** `Click the Google Search button`
    *   **Expected Action:** `click` with a selector targeting the search button (e.g., `input[name='btnK']`, `button:has-text('Google Search')` - depends on exact button). *Note: Sometimes pressing Enter after typing is implicitly handled or might require a separate command/logic.* Let's assume the LLM finds a clickable button.
    *   **Expected Result:** Search is executed, results page loads. Success=True, URL changes.

4.  **Command:** `Click the first search result link`
    *   **Expected Action:** `click` with selector `div#search a:has(h3):first-of-type` (using the special instruction).
    *   **Expected Result:** Browser navigates to the first organic search result page. Success=True, URL changes.

5.  **Command:** `scroll down`
    *   **Expected Action:** `scroll` with `direction="down"`
    *   **Expected Result:** Page scrolls down. Success=True.

6.  **Command:** `scroll up`
    *   **Expected Action:** `scroll` with `direction="up"`
    *   **Expected Result:** Page scrolls up. Success=True.

## Test Case 2: Specific Link Click (Adapt text as needed)

1.  **Command:** `Go to playwright.dev/python`
    *   **Expected Action:** `navigate`
    *   **Expected Result:** Page loads. Success=True.

2.  **Command:** `Click the link named 'API reference'` (or similar text visible on the page)
    *   **Expected Action:** `click` with selector like `a:has-text('API reference')`
    *   **Expected Result:** Navigates to the API reference section/page. Success=True.

## Test Case 3: Input Fields

1.  **Command:** `Go to github.com/login`
    *   **Expected Action:** `navigate`
    *   **Expected Result:** GitHub login page loads. Success=True.

2.  **Command:** `Enter 'my-username' into the username field`
    *   **Expected Action:** `type` with selector like `#login_field` or `input[name='login']` and `text="my-username"`
    *   **Expected Result:** Username typed. Success=True.

3.  **Command:** `Type 'my-password' into the password input`
    *   **Expected Action:** `type` with selector like `#password` or `input[name='password']` and `text="my-password"`
    *   **Expected Result:** Password typed. Success=True.

## Test Case 4: Invalid/Ambiguous Commands

1.  **Command:** `Do something interesting`
    *   **Expected Action:** LLM fails to translate, returns None or error.
    *   **Expected Result:** Agent returns `{"success": False, "error": "LLM translation failed"}` or similar.

2.  **Command:** `Click the green button` (when multiple green buttons exist or none are green)
    *   **Expected Action:** LLM might generate a selector for *a* button, or fail.
    *   **Expected Result:** If LLM generates a selector, the click might target the wrong element or fail if selector is bad. If LLM fails, translation error. Test resilience.










Navigate to https://github.com/login
Type "" into the github username field
Type "" into the github password field
Click the github sign in button