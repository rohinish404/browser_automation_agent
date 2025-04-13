import pyautogui
import time
print("Attempting screenshot...")
try:
    start_time = time.time()
    img = pyautogui.screenshot()
    end_time = time.time()
    print(f"Screenshot taken successfully in {end_time - start_time:.2f} seconds.")
    img.save("test_screenshot.png")
    print("Screenshot saved as test_screenshot.png")
except Exception as e:
    print(f"Screenshot failed: {e}")
    import traceback
    traceback.print_exc() # Print full traceback
