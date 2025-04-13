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


## stage 2 test case

Go to 'https://github.com/login'
Type "unboxtech404" into the username field
Type "unboxtech03" into the password field
press enter
scroll down
extract: the trending repository names 



