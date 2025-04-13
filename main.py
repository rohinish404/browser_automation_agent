
import asyncio
import logging

from interaction_agent import InteractionAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():

    agent = InteractionAgent()
    try:
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

                result = await agent.interact(command)

                if result.get("success"):
                    print(f"Action successful.")
                    if "url" in result:
                        print(f"  Current URL: {result['url']}")
                else:
                    print(f"Action failed: {result.get('error', 'Unknown error')}")

                print("-" * 20)

            except KeyboardInterrupt:
                logger.info("\nKeyboard interrupt detected. Exiting...")
                break
            except Exception as e:
                logger.error(f"An error occurred in the main loop: {e}", exc_info=True)
                print(f"An unexpected error occurred: {e}")

    except Exception as e:
        logger.error(f"Failed to initialize or run the agent: {e}", exc_info=True)
        print(f"Critical error during setup: {e}")
    finally:
        logger.info("Shutting down agent...")
        await agent.close()
        logger.info("Agent shutdown complete.")
        print("Browser closed. Exiting program.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting program due to user interrupt.")