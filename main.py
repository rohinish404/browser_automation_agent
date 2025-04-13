# main.py
import asyncio
import logging
import argparse

from interaction_agent import InteractionAgent # Added for command-line arguments


# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Optional: Set pyautogui logging level if needed
# logging.getLogger('pyautogui').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Command Line Argument Parsing ---
parser = argparse.ArgumentParser(description="Run Browser Navigation Agent with OS Control")
parser.add_argument(
    "--proxy",
    type=str,
    default=None,
    help="Proxy server configuration string (e.g., 'http://user:pass@host:port' or 'socks5://host:port')"
)
parser.add_argument(
    "--load-extension",
    type=str,
    nargs='*', # Allows multiple extension paths
    default=None,
    help="Paths to unpacked browser extensions to load"
)
parser.add_argument(
    "--start-url",
    type=str,
    default="https://www.google.com", # Start with Google by default
    help="The initial URL to navigate to when the browser starts"
)
args = parser.parse_args()
# --- End Argument Parsing ---

async def main():
    # --- Instantiate the agent with proxy/extension config ---
    agent = InteractionAgent(proxy_config=args.proxy, extension_paths=args.load_extension)
    try:
        # Setup the agent (which internally sets up the OS controller and launches browser)
        # Pass the starting URL
        agent.setup(initial_url=args.start_url)

        print("\nBrowser Navigation Agent Initialized (OS Control Mode).")
        print("Enter commands for OS-level browser interaction (e.g., 'Navigate to google.com', 'Click the search bar', 'Type hello world', 'Extract the main headline').")
        print("Use visual descriptions for click/type targets (e.g., 'Click the Login button').")
        print("Type 'extract: <your query>' to extract data.")
        print("Type 'quit' to exit.")

        while True:
            try:
                command_input = input("> ")
                if not command_input:
                    continue
                if command_input.lower() in ['quit', 'exit']:
                    logger.info("Exit command received.")
                    break

                result = {}
                # --- Handle Extraction Command ---
                if command_input.lower().startswith("extract:"):
                    query = command_input[len("extract:"):].strip()
                    if not query:
                        print("Please provide a query after 'extract:'. Example: 'extract: the price'")
                        continue
                    print(f"--- Performing Extraction: '{query}' ---")
                    # Use the agent's extract method
                    result = await agent.extract(query) # Extractor is async
                    print("--- Extraction Result ---")
                    print(json.dumps(result, indent=2))
                    print("-" * 20)
                    continue # Go to next loop iteration after extraction

                # --- Handle Interaction Command ---
                print(f"--- Sending Command: '{command_input}' ---")
                # Use the agent's interact method (now uses OSController)
                # interact is synchronous in this OS control example
                result = agent.interact(command_input)

                # Provide user feedback based on the result
                if result.get("success"):
                    print(f"Action successful.")
                else:
                    print(f"Action failed: {result.get('error', 'Unknown OS control error')}")

                print("-" * 20)

            except KeyboardInterrupt:
                logger.info("\nKeyboard interrupt detected. Exiting...")
                break
            except Exception as e:
                logger.error(f"An error occurred in the main loop: {e}", exc_info=True)
                print(f"An unexpected error occurred: {e}")

    except Exception as e:
        logger.error(f"Failed to initialize or run the agent: {e}", exc_info=True)
        print(f"Critical error during setup or run: {e}")
    finally:
        logger.info("Shutting down agent...")
        agent.close() # Uses OSController teardown
        logger.info("Agent shutdown complete.")
        print("Browser closed (OS control). Exiting program.")


if __name__ == "__main__":
    # Pyautogui might have issues in some environments, this is a basic run structure
    # Note: Since OSController is mostly synchronous, running its methods directly
    # from the agent's interact method might be simpler than full asyncio if
    # the translator itself doesn't require async deeply. Here, we kept main async
    # primarily because the extractor *could* be async.
    try:
       asyncio.run(main())
    except KeyboardInterrupt:
       print("\nExiting program due to user interrupt.")
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        print(f"An unhandled error occurred: {e}")