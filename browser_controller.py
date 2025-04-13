# browser_controller.py
import asyncio
from playwright.async_api import async_playwright, Browser, Page, Playwright, Locator

ELEMENT_TIMEOUT = 10000 # Increased to 10 seconds

class AsyncBrowserController:
    def __init__(self):
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    async def setup(self, headless=False):
        print("Setting up browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        context = await self.browser.new_context()
        self.page = await context.new_page()
        print("Browser setup complete.")
        return self.page

    async def teardown(self):
        print("Tearing down browser...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("Browser teardown complete.")

    async def navigate(self, url: str):
        if not self.page: raise Exception("Page not initialized")
        print(f"Navigating to: {url}")
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000) # Increased timeout
            print(f"Navigation successful.")
            return {"success": True, "url": self.page.url}
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            return {"success": False, "error": str(e)}


    async def scroll(self, direction: str):
        if not self.page: raise Exception("Page not initialized")
        print(f"Scrolling {direction}")
        try:
            if direction == "down":
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            elif direction == "up":
                 await self.page.evaluate("window.scrollBy(0, -window.innerHeight)")
            await asyncio.sleep(0.5) # Wait for scroll
            print("Scroll successful.")
            return {"success": True}
        except Exception as e:
            print(f"Error scrolling: {e}")
            return {"success": False, "error": str(e)}

    async def _extract_element_details(self, locator: Locator) -> dict | None:
        """Extracts key details from a Playwright Locator."""
        try:
            # Ensure the first match is visible before extracting
            await locator.first.wait_for(state="visible", timeout=1000) # Quick visibility check

            element = locator.first # Work with the first match
            tag = await element.evaluate('el => el.tagName.toLowerCase()')
            attrs = {
                'text': await element.text_content() or "",
                'id': await element.get_attribute('id') or "",
                'name': await element.get_attribute('name') or "",
                'placeholder': await element.get_attribute('placeholder') or "",
                'aria-label': await element.get_attribute('aria-label') or "",
                'type': await element.get_attribute('type') or "",
                'role': await element.get_attribute('role') or "",
                'value': await element.evaluate('el => el.value', timeout=500) or "", # Get current value for inputs
            }
             # Filter out empty attributes for brevity
            details = {k: v for k, v in attrs.items() if v}
            details['tag'] = tag
            return details
        except Exception as e:
            # Ignore elements that become non-visible quickly or cause errors
            # print(f"Debug: Error extracting details: {e}")
            return None

    async def get_interactive_elements(self) -> list[dict]:
        """Gets details of visible interactive elements on the page."""
        if not self.page or self.page.is_closed(): return []
        print("Extracting interactive elements...")
        elements = []
        # Common interactive element selectors
        selectors = [
            "button",
            "a[href]",
            "input:not([type='hidden'])",
            "textarea",
            "select",
            "[role='button']",
            "[role='link']",
            "[role='menuitem']",
            "[role='tab']",
            "[role='checkbox']",
            "[role='radio']",
            "[contenteditable='true']",
        ]

        max_elements = 30 # Limit to avoid overly long prompts
        count = 0

        for selector in selectors:
            if count >= max_elements: break
            try:
                # Find all matches for the selector
                locator = self.page.locator(selector)
                num_matches = await locator.count()

                for i in range(num_matches):
                    if count >= max_elements: break
                    try:
                        element_locator = locator.nth(i)
                        details = await self._extract_element_details(element_locator)
                        if details:
                            elements.append(details)
                            count += 1
                    except Exception as inner_e:
                        # print(f"Debug: Skipping element {i} for selector '{selector}': {inner_e}")
                        continue # Skip problematic elements

            except Exception as e:
                print(f"Warning: Error locating elements with selector '{selector}': {e}")
                continue # Continue with next selector if one fails

        print(f"Extracted {len(elements)} interactive elements.")
        return elements

    async def get_current_state(self) -> dict:
        """Gets URL, Title, and basic interactive element info."""
        if not self.page or self.page.is_closed():
             return {"url": "N/A - Page Closed", "title": "N/A", "elements": []}
        try:
            url = self.page.url
            title = await self.page.title()
            elements = await self.get_interactive_elements()
            return {"url": url, "title": title, "elements": elements}
        except Exception as e:
            print(f"Error getting state: {e}")
            return {"url": "Error", "title": "Error", "elements": []}

    # --- Methods requiring accurate selectors ---
    async def click(self, selector: str):
        if not self.page: raise Exception("Page not initialized")
        print(f"Clicking selector: {selector}")
        try:
            locator = self.page.locator(selector).first # Target the first match
            await locator.wait_for(state="visible", timeout=ELEMENT_TIMEOUT)
            await locator.scroll_into_view_if_needed() # Ensure it's in view
            await locator.click(timeout=5000)
            # Wait for potential navigation or dynamic changes
            await self.page.wait_for_load_state("domcontentloaded", timeout=5000) # Wait for basic load
            await asyncio.sleep(1) # Small buffer
            print(f"Click successful.")
            return {"success": True, "url": self.page.url}
        except Exception as e:
            print(f"Error clicking {selector}: {e}")
            # Attempt a JS click as a fallback
            try:
                print("Attempting JS click fallback...")
                await self.page.locator(selector).first.evaluate("el => el.click()")
                await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                await asyncio.sleep(1)
                print("JS click fallback successful.")
                return {"success": True, "url": self.page.url}
            except Exception as js_e:
                print(f"JS click fallback failed for {selector}: {js_e}")
                return {"success": False, "error": str(e)}


    async def type(self, selector: str, text: str):
        if not self.page: raise Exception("Page not initialized")
        print(f"Typing '{text}' into selector: {selector}")
        try:
            locator = self.page.locator(selector).first # Target the first match
            await locator.wait_for(state="visible", timeout=ELEMENT_TIMEOUT)
            await locator.scroll_into_view_if_needed()
            await locator.fill(text) # Use fill for reliability
            print(f"Typing successful.")
            return {"success": True}
        except Exception as e:
            print(f"Error typing into {selector}: {e}")
            return {"success": False, "error": str(e)}
