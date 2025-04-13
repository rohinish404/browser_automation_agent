## Test case 1: Basic Google Search

1.  **Command:** `Go to google.com`
    *   **Expected Action:** `navigate` with `url="https://google.com"`
    *   **Expected Result:** Browser navigates to Google homepage. Success=True.

2.  **Command:** `Type 'Playwright testing framework' into the search bar`
    *   **Expected Result:** Text is entered into the search field. Success=True.

3.  **Command:** `Click the Google Search button`
    *   **Expected Result:** Search is executed, results page loads. Success=True, URL changes.

4.  **Command:** `Click the first search result link`
    *   **Expected Result:** Browser navigates to the first organic search result page. Success=True, URL changes.

5.  **Command:** `scroll down`
    *   **Expected Result:** Page scrolls down. Success=True.

6.  **Command:** `scroll up`
    *   **Expected Result:** Page scrolls up. Success=True.

## Test Case 2: Specific Link Click (Adapt text as needed)

1.  **Command:** `Go to playwright.dev/python`
    *   **Expected Action:** `navigate`
    *   **Expected Result:** Page loads. Success=True.

2.  **Command:** `Click the link named 'API reference'` (or similar text visible on the page)
    *   **Expected Result:** Navigates to the API reference section/page. Success=True.

## Test Case 3: Input Fields

1.  **Command:** `Go to github.com/login`
    *   **Expected Action:** `navigate`
    *   **Expected Result:** GitHub login page loads. Success=True.

2.  **Command:** `Enter 'my-username' into the username field`
    *   **Expected Result:** Username typed. Success=True.

3.  **Command:** `Type 'my-password' into the password input`
    *   **Expected Result:** Password typed. Success=True.
