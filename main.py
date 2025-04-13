# main.py
import asyncio
import logging

from interaction_agent import InteractionAgent
# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    # Instantiate the agent that encapsulates controller and translation
    agent = InteractionAgent()
    try:
        # Setup the agent (which internally sets up the browser)
        # Set headless=True for background operation, False for visible browser
        await agent.setup(headless=False)

        print("\nBrowser Navigation Agent Initialized.")
        print("Enter your commands below (e.g., 'Go to google.com', 'Type 'playwright' into the search bar', 'Click the first search result', 'scroll down', 'quit').")

        while True:
            try:
                command = input("> ")
                if not command:
                    continue
                if command.lower() in ['quit', 'exit']:
                    logger.info("Exit command received.")
                    break

                # Use the agent's interact method
                result = await agent.interact(command)

                # Provide user feedback based on the result
                if result.get("success"):
                    print(f"Action successful.")
                    # Optionally print specific results like new URL
                    if "url" in result:
                        print(f"  Current URL: {result['url']}")
                else:
                    print(f"Action failed: {result.get('error', 'Unknown error')}")

                print("-" * 20)

            except KeyboardInterrupt:
                logger.info("\nKeyboard interrupt detected. Exiting...")
                break
            except Exception as e:
                # Catch unexpected errors in the loop itself
                logger.error(f"An error occurred in the main loop: {e}", exc_info=True)
                print(f"An unexpected error occurred: {e}")
                # Decide whether to break or continue
                # break

    except Exception as e:
        # Catch errors during agent setup
        logger.error(f"Failed to initialize or run the agent: {e}", exc_info=True)
        print(f"Critical error during setup: {e}")
    finally:
        # Ensure cleanup happens
        logger.info("Shutting down agent...")
        await agent.close()
        logger.info("Agent shutdown complete.")
        print("Browser closed. Exiting program.")


if __name__ == "__main__":
    # Handle potential asyncio event loop issues on Windows/some environments
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # Uncomment if needed on Windows
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C if it happens outside the main async loop's try/except
        print("\nExiting program due to user interrupt.")