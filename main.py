# main.py
import asyncio
import logging
import argparse
import json # Make sure json is imported

from interaction_agent import InteractionAgent

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Command Line Argument Parsing ---
# ... (argument parsing remains the same) ...
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

async def main():
    agent = InteractionAgent(proxy_config=args.proxy, extension_paths=args.load_extension)
    try:
        # Setup is synchronous
        agent.setup(initial_url=args.start_url)

        print("\nBrowser Navigation Agent Initialized (OS Control Mode).")
        print("Enter commands for OS-level browser interaction (e.g., 'Navigate to google.com', 'Click the search bar', 'Type hello world', 'Extract the main headline').")
        print("Use visual descriptions for click/type targets (e.g., 'Click the Login button').")
        print("Type 'extract: <your query>' to extract data.")
        print("Type 'quit' to exit.")

        while True:
            try:
                # Use asyncio.to_thread for synchronous input in async context
                # to avoid blocking the event loop entirely while waiting for user input
                command_input = await asyncio.to_thread(input, "> ")

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
                    # Use await as agent.extract is async
                    result = await agent.extract(query)
                    print("--- Extraction Result ---")
                    # Ensure result is printable, handle potential non-JSON data
                    try:
                        print(json.dumps(result, indent=2))
                    except TypeError:
                         print(result) # Print raw if not JSON serializable
                    print("-" * 20)
                    continue

                # --- Handle Interaction Command ---
                print(f"--- Sending Command: '{command_input}' ---")
                # ******* CHANGED: Use await as agent.interact is now async *******
                result = await agent.interact(command_input)

                # Provide user feedback based on the result
                if result and result.get("success"): # Check if result is not None
                    print(f"Action successful.")
                else:
                    error_msg = "Unknown OS control error"
                    if result and result.get("error"):
                        error_msg = result.get("error")
                    print(f"Action failed: {error_msg}")

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
        # Close is synchronous
        agent.close()
        logger.info("Agent shutdown complete.")
        print("Browser closed (OS control). Exiting program.")


if __name__ == "__main__":
    try:
       asyncio.run(main())
    except KeyboardInterrupt:
       print("\nExiting program due to user interrupt.")
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        print(f"An unhandled error occurred: {e}")