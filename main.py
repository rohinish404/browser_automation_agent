# main.py
import asyncio
from browser_controller import AsyncBrowserController
from llm_translator import translate_command_to_action

async def main():
    controller = AsyncBrowserController()
    try:
        await controller.setup(headless=False) # Start non-headless for debugging

        while True:
            try:
                command = input("Enter command (or 'quit' to exit): ")
                if command.lower() == 'quit':
                    break
                if not command:
                    continue

                current_state = await controller.get_current_state()
                print(f"Current State: {current_state}")

                action_plan = await translate_command_to_action(command, current_state)

                if not action_plan:
                    print("Failed to get action plan from LLM.")
                    continue

                action_name = action_plan.get("action")
                params = action_plan.get("parameters", {})

                result = None
                if action_name == "navigate":
                    result = await controller.navigate(**params)
                elif action_name == "click":
                    result = await controller.click(**params)
                elif action_name == "type":
                    result = await controller.type(**params)
                elif action_name == "scroll":
                    result = await controller.scroll(**params)
                else:
                    print(f"Unknown action: {action_name}")
                    result = {"success": False, "error": f"Unknown action: {action_name}"}

                print(f"Action Result: {result}")
                print("-" * 20)


            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"An error occurred in the main loop: {e}")
                # Optionally attempt to recover or just break
                # break

    finally:
        await controller.teardown()

if __name__ == "__main__":
    asyncio.run(main())