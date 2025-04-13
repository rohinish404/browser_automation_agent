import pyautogui
import time
import platform
import subprocess
import logging
import base64
from io import BytesIO
import os
import pygetwindow as gw
from PIL import Image 


logger = logging.getLogger(__name__)

BROWSER_PATHS = {
    "darwin": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "win32": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "linux": "/usr/bin/google-chrome"
}
IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'images')
DEBUG_SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), 'debug_screenshots') 
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(DEBUG_SCREENSHOT_DIR, exist_ok=True) 

IMAGE_CONFIDENCE = 0.8
ACTION_DELAY = 0.7
NAV_HOTKEY_DELAY = 0.5
CLICK_TYPE_DELAY = 0.4
LOAD_DELAY = 4.0
FIND_TIMEOUT = 7

# --- Debug Flags ---
# Set to True to VISUALIZE mouse movements instead of clicking/typing
VISUALIZE_ONLY = False
# Set to True to save screenshots used during image search
SAVE_DEBUG_SCREENSHOTS = False
# --- End Debug Flags ---

class OSController:
    def __init__(self):
        self.browser_process = None
        self.system = platform.system().lower()
        pyautogui.PAUSE = 0.1
        pyautogui.FAILSAFE = True

    def _get_browser_path(self):
        path = BROWSER_PATHS.get(self.system)
        if not path or not os.path.exists(path):
            raise FileNotFoundError(
                f"Browser executable not found for {self.system}. "
                f"Please check BROWSER_PATHS in os_controller.py. Tried: {path}"
            )
        return path

    def _get_image_path(self, image_name: str) -> str:
        safe_name = "".join(c for c in image_name if c.isalnum() or c in ('_', '-')).rstrip()
        if not safe_name.endswith('.png'):
            safe_name += '.png'
        path = os.path.join(IMAGE_DIR, safe_name)
        logger.debug(f"Checking for image template at path: {path}")
        if not os.path.exists(path):
             logger.warning(f"Image file not found: {path}. Please create it in the '{IMAGE_DIR}' directory.")
        return path

    def setup(self, url: str = "about:blank", proxy_config: str | None = None, extension_paths: list[str] | None = None):
        logger.info("Launching native browser...")
        browser_path = self._get_browser_path()
        command = [browser_path]
        if proxy_config:
            command.append(f"--proxy-server={proxy_config}")
            logger.info(f"Using proxy: {proxy_config}")
        if extension_paths:
            load_extension_arg = ",".join(extension_paths)
            command.append(f"--load-extension={load_extension_arg}")
            logger.info(f"Loading extensions from: {extension_paths}")
        command.append(url)

        try:
            self.browser_process = subprocess.Popen(command)
            logger.info(f"Browser process started (PID: {self.browser_process.pid}). Waiting for window...")
            time.sleep(LOAD_DELAY * 1.5)
            if not self._activate_browser_window():
                 logger.warning("Initial browser window title check failed after launch.")
            else:
                 logger.info("Initial browser window title check successful after launch.")
            logger.info("Browser setup likely complete.")
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}", exc_info=True)
            self.browser_process = None
            return {"success": False, "error": str(e)}

    def teardown(self):
        logger.info("Closing native browser...")
        if self.browser_process:
            try:
                self.browser_process.terminate()
                try:
                     self.browser_process.wait(timeout=2)
                     logger.info("Browser terminated gracefully.")
                except subprocess.TimeoutExpired:
                     logger.warning("Browser did not terminate gracefully after 2s, killing...")
                     self.browser_process.kill()
                     logger.info("Browser killed.")
            except Exception as e:
                logger.error(f"Error closing browser process: {e}")
            finally:
                self.browser_process = None
        else:
            logger.info("Browser process not found or already closed.")
        return {"success": True}

    def _activate_browser_window(self):
        """Attempts to find *if* a likely browser window exists (Best Effort).
        """
        logger.info("--- Running FALLBACK _activate_browser_window (Title check ONLY) ---")
        try:
            possible_titles = ["Google Chrome", "Mozilla Firefox", "Microsoft Edge", "Safari", "GitHub", "New Tab", "Login"]

            all_titles = gw.getAllTitles()

            if not all_titles:
                logger.warning("PyGetWindow getAllTitles() couldn't find any window titles.")
                return False 

            found_browser_title = False
            for title in all_titles:
                 if not title: continue
                 if any(pt.lower() in title.lower() for pt in possible_titles):
                      logger.info(f"Found likely browser title: '{title}'. Assuming browser window exists.")
                      found_browser_title = True
                      break

            if not found_browser_title:
                logger.warning("Could not find any likely browser window title using getAllTitles().")
                return False

            logger.info("Browser window title found. Activation cannot be forced with this pygetwindow version.")
            return True

        except Exception as e:
            logger.error(f"General error checking for browser window title: {e}", exc_info=True)
            return False


    def _find_target(self, target_description: str) -> tuple[int, int] | None:
        """Finds a target on screen based on its description (image filename)."""
        image_path = self._get_image_path(target_description)
        if not os.path.exists(image_path):
            logger.error(f"Cannot find target '{target_description}', image file missing: {image_path}")
            return None

        logger.info(f"Looking for target '{target_description}' (using image: {os.path.basename(image_path)})...")
        start_time = time.time()
        location = None
        screenshot_pil = None

        if not self._activate_browser_window():
            logger.warning(f"Browser window title check failed before searching for '{target_description}'. Search might fail or find elements in wrong window.")
        else:
            logger.info("Browser window title check successful before search.")
            time.sleep(0.3)

        while time.time() - start_time < FIND_TIMEOUT:
            try:
                screenshot_pil = pyautogui.screenshot()
                logger.debug(f"Took screenshot (size: {screenshot_pil.size}) to find '{target_description}'")

                if SAVE_DEBUG_SCREENSHOTS:
                    try:
                        safe_desc = "".join(c for c in target_description if c.isalnum() or c in ('_', '-')).rstrip()
                        debug_filename = f"debug_screenshot_searching_{safe_desc}_{int(time.time())}.png"
                        debug_filepath = os.path.join(DEBUG_SCREENSHOT_DIR, debug_filename)
                        screenshot_pil.save(debug_filepath)
                        logger.info(f"Saved screenshot for debugging: {debug_filepath}")
                    except Exception as save_err:
                        logger.error(f"Could not save debug screenshot: {save_err}")

                region_box = pyautogui.locateOnScreen(image_path, confidence=IMAGE_CONFIDENCE)

                if region_box:
                    center_x = region_box.left + region_box.width // 2
                    center_y = region_box.top + region_box.height // 2
                    location = (center_x, center_y)
                    logger.info(f"Target '{target_description}' found. Region Box: {region_box}, Calculated Center: {location}")
                    return location

            except pyautogui.ImageNotFoundException:
                logger.debug(f"Target '{target_description}' not found in current screenshot, retrying...")
            except Exception as e:
                logger.error(f"Error during image search for '{target_description}': {e}", exc_info=True)
                return None

            time.sleep(0.6)

        logger.warning(f"Target '{target_description}' not found on screen after {FIND_TIMEOUT} seconds.")
        return None

    def _visualize_coordinates(self, coords: tuple[int, int] | None, target_description: str):
        """Moves the mouse to the coordinates for visual inspection."""
        if not coords:
            logger.warning(f"Cannot visualize coordinates for '{target_description}', they are None.")
            return

        try:
            x, y = coords
            logger.info(f"VISUALIZING: Moving mouse to {coords} for '{target_description}' (will pause for 3s)...")
            pyautogui.moveTo(x, y, duration=0.5)
            time.sleep(3.0)
            logger.info("VISUALIZING: Paused finished.")
        except Exception as e:
            logger.error(f"Error during visualization movement: {e}", exc_info=True)

    def navigate(self, url: str):
        logger.info(f"Navigating to: {url}")
        if not self._activate_browser_window():
             logger.warning("Browser window title check failed before navigation. Hotkeys might fail.")
             time.sleep(0.5)

        try:
            logger.debug("Activating address bar (hotkey)...")
            if self.system == "darwin":
                pyautogui.hotkey('command', 'l')
            else:
                pyautogui.hotkey('ctrl', 'l')
            time.sleep(NAV_HOTKEY_DELAY)

            logger.debug("Clearing address bar (selecting all + backspace)...")
            if self.system == "darwin":
                 pyautogui.hotkey('command', 'a')
            else:
                 pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('backspace')
            time.sleep(0.1)

            logger.debug(f"Typing URL: {url}")
            pyautogui.write(url, interval=0.02)
            time.sleep(ACTION_DELAY / 2)

            logger.debug("Pressing Enter...")
            pyautogui.press('enter')
            logger.info(f"Navigation to {url} initiated. Waiting for page load...")
            time.sleep(LOAD_DELAY)
            logger.info("Navigation likely complete.")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error during navigation to {url}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def click(self, target_description: str):
        logger.info(f"Attempting to click: {target_description}")
        coords = self._find_target(target_description)

        if coords:
            if VISUALIZE_ONLY:
                self._visualize_coordinates(coords, target_description)
                logger.info(f"VISUALIZE_ONLY=True. Skipping actual click for '{target_description}'.")
                return {"success": True, "visualized_only": True}

            logger.info(f"Coordinates found for '{target_description}': {coords}. Proceeding with click (assuming window has focus).")
            time.sleep(0.5)

            try:
                click_x, click_y = coords
                logger.info(f"Moving mouse to {coords} for clicking {target_description}...")
                pyautogui.moveTo(click_x, click_y, duration=0.15)
                time.sleep(CLICK_TYPE_DELAY / 2)

                logger.info(f"Clicking on '{target_description}' at {coords}.")
                pyautogui.click()
                time.sleep(CLICK_TYPE_DELAY)
                logger.info(f"Click action for '{target_description}' completed.")
                return {"success": True}
            except Exception as e:
                 logger.error(f"Error clicking {target_description} at {coords}: {e}", exc_info=True)
                 return {"success": False, "error": f"Error during click action: {str(e)}"}
        else:
            err = f"Target '{target_description}' not found for clicking."
            return {"success": False, "error": err}

    def type(self, text: str, target_description: str):
        logger.info(f"Attempting to type '{text[:20]}...' into {target_description}")
        coords = self._find_target(target_description)

        if coords:
            if VISUALIZE_ONLY:
                self._visualize_coordinates(coords, f"{target_description} (before typing)")
                logger.info(f"VISUALIZE_ONLY=True. Skipping actual click/type for '{target_description}'.")
                return {"success": True, "visualized_only": True}

            logger.info(f"Coordinates found for '{target_description}': {coords}. Proceeding with click-and-type (assuming window has focus).")
            time.sleep(0.5)

            try:
                click_x, click_y = coords
                logger.info(f"Moving mouse to {coords} for typing into {target_description}...")
                pyautogui.moveTo(click_x, click_y, duration=0.15)
                time.sleep(CLICK_TYPE_DELAY / 2)

                logger.info(f"Clicking on '{target_description}' at {coords} before typing.")
                pyautogui.click()
                time.sleep(CLICK_TYPE_DELAY)

                logger.info(f"Typing text into '{target_description}'...")
                pyautogui.write(text, interval=0.03)
                time.sleep(ACTION_DELAY / 2)
                logger.info(f"Type action for '{target_description}' completed.")
                return {"success": True}
            except Exception as e:
                logger.error(f"Error typing into {target_description} at {coords}: {e}", exc_info=True)
                return {"success": False, "error": f"Error during type action: {str(e)}"}
        else:
            err = f"Target '{target_description}' not found for typing."
            return {"success": False, "error": err}

    def scroll(self, direction: str):
        logger.info(f"Scrolling {direction}")
        if not self._activate_browser_window():
             logger.warning("Browser window title check failed before scrolling. Scroll might target wrong window.")
             time.sleep(0.5)

        try:
            scroll_amount = 250

            if direction == "down":
                logger.debug(f"Scrolling down by {-scroll_amount} units")
                pyautogui.scroll(-scroll_amount)
            elif direction == "up":
                logger.debug(f"Scrolling up by {scroll_amount} units")
                pyautogui.scroll(scroll_amount)
            else:
                 logger.warning(f"Invalid scroll direction: {direction}")
                 return {"success": False, "error": f"Invalid scroll direction: {direction}"}
            
            time.sleep(ACTION_DELAY / 3)
            logger.info(f"Scroll {direction} completed.")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error scrolling {direction}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def press_key(self, key_name: str):
        logger.info(f"Pressing key: {key_name}")
        if not self._activate_browser_window():
             logger.warning(f"Browser window title check failed before pressing key '{key_name}'. Key press might target wrong window.")
             time.sleep(0.5)

        valid_keys = pyautogui.KEYBOARD_KEYS
        lower_key = key_name.lower()
        if lower_key not in valid_keys:
             if lower_key == 'enter': lower_key = 'enter'
             elif lower_key == 'esc': lower_key = 'esc'
             elif lower_key == 'tab': lower_key = 'tab'
             elif lower_key == 'page_down': lower_key = 'pagedown'
             elif lower_key == 'page_up': lower_key = 'pageup'
             else:
                 logger.error(f"Invalid or unsupported key name: '{key_name}'. Check pyautogui.KEYBOARD_KEYS or add an alias.")
                 return {"success": False, "error": f"Invalid or unsupported key name: {key_name}"}

        try:
            logger.info(f"Pressing key: {lower_key}")
            pyautogui.press(lower_key)
            logger.info(f"Key '{lower_key}' pressed successfully.")
            time.sleep(ACTION_DELAY / 2)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error pressing key '{lower_key}': {e}", exc_info=True)
            return {"success": False, "error": str(e)}


    def get_current_state(self) -> dict:
        logger.info("Getting current screen state...")
        if not self._activate_browser_window():
             logger.warning("Browser window title check failed before taking screenshot. Content might be wrong.")
             time.sleep(0.5)

        screenshot_base64 = None
        visible_text = None
        url = "unknown - OS control"
        title = "unknown - OS control"

        try:
            screenshot_pil = pyautogui.screenshot()
            logger.info("Screenshot captured for get_current_state.")

            if SAVE_DEBUG_SCREENSHOTS:
                 try:
                     debug_filename = f"debug_screenshot_get_state_{int(time.time())}.png"
                     debug_filepath = os.path.join(DEBUG_SCREENSHOT_DIR, debug_filename)
                     screenshot_pil.save(debug_filepath)
                     logger.info(f"Saved get_state screenshot: {debug_filepath}")
                 except Exception as save_err:
                     logger.error(f"Could not save get_state debug screenshot: {save_err}")

            buffered = BytesIO()
            screenshot_pil.save(buffered, format="PNG")
            screenshot_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            try:
                import pytesseract
                visible_text = pytesseract.image_to_string(screenshot_pil)
                logger.info("OCR performed on screenshot.")
            except ImportError:
                 logger.warning("pytesseract not installed, OCR skipped.")
                 visible_text = "OCR skipped: pytesseract not installed."
            except Exception as ocr_error:
                if "Tesseract is not installed or" in str(ocr_error):
                     logger.error("OCR failed: Tesseract not found or not in PATH. Please install it: https://tesseract-ocr.github.io/tessdoc/Installation.html", exc_info=False)
                     visible_text = "OCR Error: Tesseract not found/configured."
                else:
                    logger.warning(f"OCR failed: {ocr_error}", exc_info=True)
                    visible_text = f"OCR Error: {ocr_error}"

        except Exception as e:
            logger.error(f"Error getting screen state: {e}", exc_info=True)
            return {"url": "Error", "title": "Error", "visible_text": f"Error capturing state: {e}", "screenshot_base64": None}

        return {"url": url, "title": title, "visible_text": visible_text, "screenshot_base64": screenshot_base64}