
import asyncio
from playwright.async_api import async_playwright, Browser, Page, Playwright, Locator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


ELEMENT_TIMEOUT = 10000 

class AsyncBrowserController:
    def __init__(self):
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    async def setup(self, headless=False):
        logger.info("Setting up browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        context = await self.browser.new_context()
        self.page = await context.new_page()
        logger.info("Browser setup complete.")
        return self.page

    async def teardown(self):
        logger.info("Tearing down browser...")
        if self.page and not self.page.is_closed():
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.page = None
        self.browser = None
        self.playwright = None
        logger.info("Browser teardown complete.")

    async def navigate(self, url: str):
        if not self.page or self.page.is_closed():
            logger.error("Navigate failed: Page not initialized or closed.")
            raise Exception("Page not initialized or closed")
        logger.info(f"Navigating to: {url}")
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            logger.info(f"Navigation successful. Current URL: {self.page.url}")
            return {"success": True, "url": self.page.url}
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return {"success": False, "error": str(e)}


    async def scroll(self, direction: str):
        if not self.page or self.page.is_closed():
            logger.error("Scroll failed: Page not initialized or closed.")
            raise Exception("Page not initialized or closed")
        logger.info(f"Scrolling {direction}")
        try:
            if direction == "down":
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            elif direction == "up":
                 await self.page.evaluate("window.scrollBy(0, -window.innerHeight)")
            else:
                logger.warning(f"Invalid scroll direction: {direction}")
                return {"success": False, "error": f"Invalid direction: {direction}"}
            await asyncio.sleep(0.5)
            logger.info("Scroll successful.")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
            return {"success": False, "error": str(e)}

    async def _extract_element_details(self, locator: Locator) -> dict | None:
        """Extracts key details from a Playwright Locator."""
        try:
            await locator.first.wait_for(state="visible", timeout=500)

            element = locator.first
            tag = await element.evaluate('el => el.tagName.toLowerCase()')
            attrs = {
                'text': await element.text_content(timeout=500) or "",
                'id': await element.get_attribute('id', timeout=500) or "",
                'name': await element.get_attribute('name', timeout=500) or "",
                'placeholder': await element.get_attribute('placeholder', timeout=500) or "",
                'aria-label': await element.get_attribute('aria-label', timeout=500) or "",
                'type': await element.get_attribute('type', timeout=500) or "",
                'role': await element.get_attribute('role', timeout=500) or "",
                'value': await element.evaluate('el => el.value', timeout=500) or "",
            }
            details = {k: v for k, v in attrs.items() if v}
            details['tag'] = tag
            return details
        except Exception as e:
            return None

    async def get_interactive_elements(self) -> list[dict]:
        """Gets details of visible interactive elements on the page."""
        if not self.page or self.page.is_closed(): return []
        logger.info("Extracting interactive elements...")
        elements = []
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

        max_elements = 30
        count = 0

        element_tasks = []

        all_locators = []
        for selector in selectors:
            try:
                locator = self.page.locator(selector)
                all_locators.append(locator)
            except Exception as e:
                 logger.warning(f"Could not create locator for selector '{selector}': {e}")


        locator_results = await asyncio.gather(
            *[loc.all() for loc in all_locators],
            return_exceptions=True
        )

        for i, result in enumerate(locator_results):
            if isinstance(result, Exception):
                logger.warning(f"Error fetching elements for selector group {i}: {result}")
                continue
            if count >= max_elements: break
            for element_handle in result:
                 if count >= max_elements: break
                 try:
                     pass 
                 except Exception as e:
                     pass


        for selector in selectors:
             if count >= max_elements: break
             try:
                 locator = self.page.locator(selector)
                 num_matches = await locator.count()
                 for i in range(num_matches):
                     if count >= max_elements: break
                     try:
                         element_locator = locator.nth(i)
                         if await element_locator.is_visible(timeout=500):
                             details = await self._extract_element_details(element_locator)
                             if details:
                                 elements.append(details)
                                 count += 1
                     except Exception as inner_e:
                         continue
             except Exception as e:
                 logger.warning(f"Error locating elements with selector '{selector}': {e}")
                 continue


        logger.info(f"Extracted {len(elements)} interactive elements.")
        return elements


    async def get_current_state(self) -> dict:
        """Gets URL, Title, and basic interactive element info."""
        if not self.page or self.page.is_closed():
             logger.warning("Attempted to get state from closed or uninitialized page.")
             return {"url": "N/A - Page Closed", "title": "N/A", "elements": []}
        try:
            url = self.page.url
            title = await self.page.title()
            elements = await self.get_interactive_elements()
            return {"url": url, "title": title, "elements": elements}
        except Exception as e:
            logger.error(f"Error getting current page state: {e}")
            url = "Error"
            title = "Error"
            try:
                if self.page and not self.page.is_closed():
                    url = self.page.url
                    title = await self.page.title()
            except Exception:
                pass
            return {"url": url, "title": title, "elements": []}

    async def click(self, selector: str):
        if not self.page or self.page.is_closed():
            logger.error("Click failed: Page not initialized or closed.")
            raise Exception("Page not initialized or closed")
        logger.info(f"Attempting to click selector: {selector}")
        try:
            locator = self.page.locator(selector).first
            await locator.wait_for(state="visible", timeout=ELEMENT_TIMEOUT)
            await locator.hover(timeout=2000)
            await asyncio.sleep(0.1)
            await locator.scroll_into_view_if_needed(timeout=5000)
            await locator.click(timeout=5000)
            await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            await asyncio.sleep(1)
            logger.info(f"Click successful. Current URL: {self.page.url}")
            return {"success": True, "url": self.page.url}
        except Exception as e:
            logger.error(f"Error clicking {selector}: {e}")
            try:
                logger.warning("Standard click failed. Attempting JS click fallback...")
                locator = self.page.locator(selector).first
                await locator.wait_for(state="attached", timeout=ELEMENT_TIMEOUT)
                await locator.evaluate("el => el.click()")
                await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                await asyncio.sleep(1)
                logger.info(f"JS click fallback successful. Current URL: {self.page.url}")
                return {"success": True, "url": self.page.url}
            except Exception as js_e:
                logger.error(f"JS click fallback failed for {selector}: {js_e}")
                return {"success": False, "error": f"Initial error: {e}. Fallback error: {js_e}"}


    async def type(self, selector: str, text: str):
        if not self.page or self.page.is_closed():
             logger.error("Type failed: Page not initialized or closed.")
             raise Exception("Page not initialized or closed")
        logger.info(f"Attempting to type '{text}' into selector: {selector}")
        try:
            locator = self.page.locator(selector).first # Target the first match
            await locator.wait_for(state="visible", timeout=ELEMENT_TIMEOUT)
            await locator.scroll_into_view_if_needed(timeout=5000)
            await locator.fill(text)
            logger.info(f"Typing successful.")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error typing into {selector}: {e}")
            return {"success": False, "error": str(e)}