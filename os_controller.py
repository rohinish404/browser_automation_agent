# os_controller.py
import pyautogui
import time
import platform
import subprocess
import logging
import base64
from io import BytesIO
import os
# Optional OCR:
# import pytesseract
# from PIL import Image

logger = logging.getLogger(__name__)

# --- Configuration ---
# Paths to browser executables (adjust as needed)
BROWSER_PATHS = {
    "darwin": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", # Example for macOS
    "win32": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # Example for Windows
    "linux": "/usr/bin/google-chrome"  # Example for Linux
}
# Directory for template images used by pyautogui
IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'images')
# Ensure image directory exists
os.makedirs(IMAGE_DIR, exist_ok=True)

# --- Default Image Filenames (User must create these!) ---
# Examples: address_bar.png, login_button.png, search_bar.png, search_button.png
# These MUST be created by the user taking screenshots of their specific browser/website UI

# Confidence level for image matching (adjust based on reliability)
IMAGE_CONFIDENCE = 0.8
# Timeouts and delays
ACTION_DELAY = 0.5  # Seconds to wait after most actions
LOAD_DELAY = 3.0    # Seconds to wait after navigation (very basic)
FIND_TIMEOUT = 5    # Seconds to wait trying to find an image

class OSController:
    def __init__(self):
        self.browser_process = None
        self.system = platform.system().lower()
        pyautogui.FAILSAFE = True # Move mouse to top-left corner to stop script

    def _get_browser_path(self):
        path = BROWSER_PATHS.get(self.system)
        if not path or not os.path.exists(path):
            raise FileNotFoundError(
                f"Browser executable not found for {self.system}. "
                f"Please check BROWSER_PATHS in os_controller.py. Tried: {path}"
            )
        return path

    def _get_image_path(self, image_name: str) -> str:
        """Constructs the full path for a template image."""
        # Basic sanitization
        safe_name = "".join(c for c in image_name if c.isalnum() or c in ('_', '-')).rstrip()
        if not safe_name.endswith('.png'):
            safe_name += '.png'
        path = os.path.join(IMAGE_DIR, safe_name)
        if not os.path.exists(path):
             logger.warning(f"Image file not found: {path}. Please create it in the '{IMAGE_DIR}' directory.")
             # Optionally raise an error or return None depending on desired strictness
             # raise FileNotFoundError(f"Required image not found: {path}")
        return path

    def setup(self, url: str = "about:blank", proxy_config: str | None = None, extension_paths: list[str] | None = None):
        """Launches the native browser."""
        logger.info("Launching native browser...")
        browser_path = self._get_browser_path()
        command = [browser_path]

        # --- Add Proxy ---
        if proxy_config:
            # Example: "http://user:pass@host:port" or "socks5://host:port"
            # Note: Authentication might require extensions or more complex setups.
            command.append(f"--proxy-server={proxy_config}")
            logger.info(f"Using proxy: {proxy_config}")

        # --- Add Extensions ---
        if extension_paths:
            load_extension_arg = ",".join(extension_paths)
            command.append(f"--load-extension={load_extension_arg}")
            logger.info(f"Loading extensions from: {extension_paths}")

        # --- Add Initial URL ---
        command.append(url) # Open initial URL

        try:
            # Start the browser process
            self.browser_process = subprocess.Popen(command)
            logger.info(f"Browser process started (PID: {self.browser_process.pid}). Waiting for window...")
            # VERY basic wait - assumes browser window appears and gets focus quickly.
            # Robust implementation would need to find the window more reliably.
            time.sleep(LOAD_DELAY * 1.5)
            logger.info("Browser setup likely complete.")
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            self.browser_process = None
            return {"success": False, "error": str(e)}

    def teardown(self):
        """Closes the browser."""
        logger.info("Closing native browser...")
        if self.browser_process:
            try:
                # Try graceful termination first
                self.browser_process.terminate()
                time.sleep(1) # Give it a second
                if self.browser_process.poll() is None: # Check if still running
                    logger.warning("Browser did not terminate gracefully, killing...")
                    self.browser_process.kill()
                logger.info("Browser closed.")
            except Exception as e:
                logger.error(f"Error closing browser process: {e}")
            finally:
                self.browser_process = None
        else:
            logger.info("Browser process not found or already closed.")
        return {"success": True}

    def _find_target(self, target_description: str) -> tuple[int, int] | None:
        """
        Finds a target on screen based on its description (used as image filename).
        Tries for FIND_TIMEOUT seconds.
        """
        image_path = self._get_image_path(target_description)
        if not os.path.exists(image_path):
            logger.error(f"Cannot find target '{target_description}', image file missing: {image_path}")
            return None

        logger.info(f"Looking for target '{target_description}' (using image: {os.path.basename(image_path)})...")
        start_time = time.time()
        while time.time() - start_time < FIND_TIMEOUT:
            try:
                # Using locateCenterOnScreen which returns center coordinates directly
                location = pyautogui.locateCenterOnScreen(image_path, confidence=IMAGE_CONFIDENCE)
                if location:
                    logger.info(f"Target '{target_description}' found at: {location}")
                    # location is already a tuple (x, y) from locateCenterOnScreen
                    return location.x, location.y
            except pyautogui.ImageNotFoundException:
                pass # Keep trying
            except Exception as e:
                # Log other errors like permission issues on Linux/macOS
                logger.error(f"Error during image search for '{target_description}': {e}")
                # Don't retry indefinitely on unexpected errors
                return None
            time.sleep(0.5) # Wait a bit before retrying

        logger.warning(f"Target '{target_description}' not found on screen after {FIND_TIMEOUT} seconds.")
        return None

    def navigate(self, url: str):
        """Navigates to a URL using keyboard shortcuts."""
        logger.info(f"Navigating to: {url}")
        try:
            # 1. Activate address bar (Cmd+L on Mac, Ctrl+L on Win/Linux)
            if self.system == "darwin":
                pyautogui.hotkey('command', 'l')
            else:
                pyautogui.hotkey('ctrl', 'l')
            time.sleep(ACTION_DELAY / 2)

            # 2. Type URL
            pyautogui.write(url, interval=0.01) # Add slight typing delay
            time.sleep(ACTION_DELAY / 2)

            # 3. Press Enter
            pyautogui.press('enter')
            logger.info(f"Navigation to {url} initiated. Waiting for page load...")
            time.sleep(LOAD_DELAY) # Basic wait
            logger.info("Navigation likely complete.")
            # TODO: Add more robust wait (e.g., watch screen for changes)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error during navigation to {url}: {e}")
            return {"success": False, "error": str(e)}

    def click(self, target_description: str):
        """Clicks on a target identified by its description (image filename)."""
        logger.info(f"Attempting to click: {target_description}")
        coords = self._find_target(target_description)
        if coords:
            try:
                pyautogui.click(coords[0], coords[1])
                logger.info(f"Clicked on {target_description} at {coords}.")
                time.sleep(ACTION_DELAY) # Wait after click
                return {"success": True}
            except Exception as e:
                 logger.error(f"Error clicking {target_description} at {coords}: {e}")
                 return {"success": False, "error": str(e)}
        else:
            err = f"Target '{target_description}' not found for clicking."
            logger.error(err)
            return {"success": False, "error": err}

    def type(self, text: str, target_description: str):
        """Clicks on a target and types text into it."""
        logger.info(f"Attempting to type '{text[:20]}...' into {target_description}")
        coords = self._find_target(target_description)
        if coords:
            try:
                pyautogui.click(coords[0], coords[1])
                time.sleep(ACTION_DELAY / 2) # Short wait after click before typing
                pyautogui.write(text, interval=0.01)
                logger.info(f"Typed '{text[:20]}...' into {target_description} at {coords}.")
                time.sleep(ACTION_DELAY / 2)
                return {"success": True}
            except Exception as e:
                logger.error(f"Error typing into {target_description} at {coords}: {e}")
                return {"success": False, "error": str(e)}
        else:
            err = f"Target '{target_description}' not found for typing."
            logger.error(err)
            return {"success": False, "error": err}

    def scroll(self, direction: str):
        """Scrolls the page up or down."""
        logger.info(f"Scrolling {direction}")
        try:
            scroll_amount = 10 # Adjust scroll amount/speed as needed
            if direction == "down":
                pyautogui.scroll(-scroll_amount)
            elif direction == "up":
                pyautogui.scroll(scroll_amount)
            else:
                 logger.warning(f"Invalid scroll direction: {direction}")
                 return {"success": False, "error": f"Invalid scroll direction: {direction}"}
            time.sleep(ACTION_DELAY / 2) # Wait after scroll
            return {"success": True}
        except Exception as e:
            logger.error(f"Error scrolling {direction}: {e}")
            return {"success": False, "error": str(e)}

    # +++ NEW METHOD +++
    def press_key(self, key_name: str):
        """Presses a single key (e.g., 'enter', 'tab', 'esc')."""
        logger.info(f"Pressing key: {key_name}")
        # List of valid keys pyautogui recognizes:
        # https://pyautogui.readthedocs.io/en/latest/keyboard.html#keyboard-keys
        valid_keys = pyautogui.KEYBOARD_KEYS
        if key_name.lower() not in valid_keys:
             # Also allow common variations like "enter" for "return" on mac etc.
             if key_name.lower() == 'enter':
                 key_name = 'enter' # pyautogui handles enter correctly cross-platform
             elif key_name.lower() == 'esc':
                  key_name = 'esc'
             # Add more aliases if needed
             else:
                 logger.error(f"Invalid key name: '{key_name}'. Must be one of {valid_keys}")
                 return {"success": False, "error": f"Invalid key name: {key_name}"}

        try:
            pyautogui.press(key_name.lower())
            logger.info(f"Key '{key_name}' pressed successfully.")
            time.sleep(ACTION_DELAY) # Wait after key press
            return {"success": True}
        except Exception as e:
            logger.error(f"Error pressing key '{key_name}': {e}")
            return {"success": False, "error": str(e)}
    # +++ END OF NEW METHOD +++

    def get_current_state(self) -> dict:
        """
        Gets the current state by taking a screenshot and optionally performing OCR.
        NOTE: OCR is commented out by default as it requires Tesseract installation.
        """
        logger.info("Getting current screen state...")
        screenshot = None
        screenshot_base64 = None
        visible_text = None
        url = "unknown - OS control"
        title = "unknown - OS control"

        try:
            # 1. Take Screenshot
            screenshot_pil = pyautogui.screenshot()
            buffered = BytesIO()
            screenshot_pil.save(buffered, format="PNG")
            screenshot_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            logger.info("Screenshot captured.")

            # 2. Optional: OCR for Visible Text (Requires Tesseract)
            try:
            #     # Ensure Pillow is installed: pip install Pillow
            #     # Ensure Tesseract is installed and in PATH: https://tesseract-ocr.github.io/tessdoc/Installation.html
                import pytesseract 
                visible_text = pytesseract.image_to_string(screenshot_pil)
                logger.info("OCR performed on screenshot.")
                # logger.debug(f"OCR Text: {visible_text[:100]}...") # Log snippet
            except Exception as ocr_error:
                logger.warning(f"OCR failed: {ocr_error}. Tesseract might not be installed or configured correctly.")
                visible_text = f"OCR Error: {ocr_error}"

            # 3. Optional: Attempt to get URL/Title (Highly Unreliable with basic tools)
            #    - Could try OCRing specific screen regions if title bar/address bar locations are known.
            #    - Could use platform-specific Accessibility APIs for better results.
            # For now, we stick to "unknown".

        except Exception as e:
            logger.error(f"Error getting screen state: {e}")
            return {"url": "Error", "title": "Error", "visible_text": f"Error capturing state: {e}", "screenshot_base64": None}

        return {"url": url, "title": title, "visible_text": visible_text, "screenshot_base64": screenshot_base64}