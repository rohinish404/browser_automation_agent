## AI Agent for Browser Automation

### Level 1
```
Minimum requirement:
Implement an interact API that accepts natural language commands to control browser actions
Properly handle common error scenarios with clear error messages
 interact API should not be website specific
An example of a successful demonstration of interact API may look like:
Log into a popular website
Perform a search with user-specified keywords
Navigate through search results and interact with a specific result item
```


## Setup

1.  **Prerequisites:**
    *   Python 3.8+
    *   Access to the Groq API (or another OpenAI-compatible API endpoint)

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/rohinish404/browser_automation_agent.git
    cd browser_automation_agent
    ```

3.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install playwright openai python-dotenv
    ```
    *   `playwright`: For browser automation.
    *   `openai`: To interact with the Groq API (using OpenAI's client library structure).
    *   `python-dotenv`: To load environment variables from a `.env` file.

5.  **Install Playwright Browsers:**
    Run this command once to download the necessary browser binaries (e.g., Chromium):
    ```bash
    playwright install
    ```

## Configuration

1.  **API Key:**
    *   You need an API key from [GroqCloud](https://console.groq.com/keys) (or your chosen LLM provider).
    *   Create a file named `.env` in the root of the `browser_navigation_agent` directory.
    *   Add your API key to the `.env` file like this:
        ```env
        GROQ_API_KEY=your_groq_api_key_here
        ```

## Running the Agent

1.  Ensure your virtual environment is activated and the `.env` file is configured.
2.  Run the main script from the terminal:
    ```bash
    python main.py
    ```
3.  The script will initialize the agent, open a browser window, and present you with a `>` prompt.
4.  Enter commands. Take from test.md file.
5.  The agent will attempt to translate and execute your command, printing the success status and current URL upon completion or an error message if it fails.
6.  Type `quit` or `exit` (or press `Ctrl+C`) to close the browser and terminate the program.

### Level 2

```
All Level 1 requirements, plus:
Enhance the interact API to directly control native browsers on your machine (Chrome/Firefox), rather than relying on third-party browser automation frameworks
When controlling browsers, the agent should use OS level APIs to interact with natively installed browsers
Ex: Do not interact with browser with browser level APIs but with point and click
Implement an extract API to retrieve structured data from web pages
Demonstrate at least one complete automation flow using both APIs:
Log into a popular website
Perform a search with user-specified keywords
Navigate through search results
Parse necessary information in a structured format
Support for the following:
Proxy configuration
Browser extension integration

```


## Setup

1.  **Prerequisites:**
    *   Python 3.8+
    *   Access to the Groq API (or another OpenAI-compatible API endpoint).
    *   **Tesseract OCR Engine:** This must be installed separately on your system.
        *   **macOS:** `brew install tesseract`
        *   **Ubuntu/Debian:** `sudo apt update && sudo apt install tesseract-ocr`
        *   **Windows:** Download installer from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki). Ensure Tesseract is added to your system's PATH during installation.
        *   Verify installation by opening a terminal/command prompt and running `tesseract --version`.
    *   A supported web browser (e.g., Google Chrome) installed in the default location expected by `os_controller.py` (adjust `BROWSER_PATHS` if needed).

2.  **Clone the Repository(specifically the stage2 branch):**
    ```bash
    git clone -b stage2 https://github.com/rohinish404/browser_automation_agent.git
    cd browser_navigation_agent
    ```

3.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install pyautogui pygetwindow Pillow pytesseract openai python-dotenv opencv-python
    ```
    *   `pyautogui`: Core GUI automation library.
    *   `pygetwindow`: Used to find window titles (best-effort activation).
    *   `Pillow`: Image processing library (dependency for pyautogui/pytesseract).
    *   `pytesseract`: Python wrapper for Tesseract OCR.
    *   `openai`: To interact with the Groq API.
    *   `python-dotenv`: To load environment variables.
    *   `opencv-python`: Required by `pyautogui` for faster image recognition.

## Image Templates

The OS controller relies on image recognition. You **MUST** create template images for the UI elements the agent needs to interact with.

1.  **Create an `images/` directory** inside the `browser_navigation_agent` folder if it doesn't exist.
2.  **Take screenshots** of the specific UI elements you want the agent to click or type into (e.g., a login button, a search input field, a specific link). 
3.  **Crop these screenshots precisely** to show only the target element.
4.  **Save these cropped images as PNG files** inside the `images/` directory.
5.  **Name the files descriptively**, matching the `target_description` the LLM is likely to generate based on your commands.
    *   Example: If you tell the agent `Click the Login button`, the LLM should output `target_description: "Login button"`. You need a corresponding `images/Login_button.png` file.
    *   Use underscores or hyphens, avoid spaces or special characters in filenames.
    *   Examples: `google_search_bar.png`, `submit_button.png`, `username_field.png`, `first_result_link_area.png`.
For demo purposes, i had the images of github username, passoword and button fields.

## Configuration

1.  **API Key:**
    *   Create a file named `.env` in the root of the `browser_navigation_agent` directory.
    *   Add your Groq API key:
        ```env
        GROQ_API_KEY=your_groq_api_key_here
        ```

2.  **Command-Line Options:**
    *   `--proxy`: Specify a proxy server (e.g., `--proxy http://user:pass@host:port`).
    *   `--load-extension`: Provide paths to unpacked extensions (e.g., `--load-extension /path/to/ext1 /path/to/ext2`).
    *   `--start-url`: Set the initial URL (e.g., `--start-url https://github.com`).

## Running the Agent

1.  Ensure your virtual environment is activated, Tesseract is installed, the `.env` file is configured, and you have created the necessary image templates in the `images/` directory.
2.  Run the main script from the terminal, optionally adding arguments:
    ```bash
    python main.py [--proxy <proxy_string>] [--load-extension <path1> <path2>] [--start-url <url>]
    ```
    Example:
    ```bash
    python main.py
    ```
3.  The script will launch the native browser and present you with a `>` prompt.
4.  Enter commands. Take examples from test.md.
5.  The agent will attempt to find the image template, perform the action, and report success/failure. Extraction results will be printed as JSON.
6.  Type `quit` or `exit` (or press `Ctrl+C`) to close the browser and terminate the program.

## How it Works (Level 2 Flow)

1.  **User Input:** You provide a command (e.g., "Click the login button") or an extraction query (`extract: Get the price`) in the terminal running `main.py`.
2.  **State Retrieval:** `InteractionAgent` calls `OSController.get_current_state()`. `OSController` takes a screenshot (`pyautogui`), performs OCR (`pytesseract`) to get `visible_text`.
3.  **LLM Interaction:**
    *   **For Commands:** `InteractionAgent` sends the command and state (`visible_text`) to `llm_translator`. The LLM (using the OS-control prompt) returns a structured OS action (e.g., `{"action": "click", "parameters": {"target_description": "login button"}}`).
    *   **For Extraction:** `InteractionAgent` sends the query and state (`visible_text`) to `extractor`. The LLM (using the extraction prompt) analyzes the text and returns extracted data as JSON.
4.  **Execution (Commands):** `InteractionAgent` calls the corresponding `OSController` method (e.g., `controller.click(target_description="login button")`).
5.  **OS Action:** `OSController` looks for `images/login_button.png` on the screen. If found, `pyautogui` moves the mouse to its center and clicks.
6.  **Feedback/Result:** The success/failure status or extracted JSON is passed back to `main.py` and displayed to you.

**This is not the perfect implementation of the browser automation ai agent but there are further rooms for improvement which i'll look into and see where things can be improved upon.**
