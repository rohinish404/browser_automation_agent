# test_groq.py
import asyncio
import os
from openai import AsyncOpenAI, OpenAIError # Import OpenAIError for better exception handling
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment
groq_api_key = os.environ.get("GROQ_API_KEY")

# --- Configuration ---
# Make sure this matches the setup in llm_translator.py
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
TEST_MODEL = "llama3-70b-8192" # Or llama3-8b-8192 for a potentially faster test
# --- End Configuration ---

async def test_api():
    """Attempts a simple API call to Groq."""
    print(f"Attempting to call Groq API (Model: {TEST_MODEL})...")

    if not groq_api_key:
        print("Error: GROQ_API_KEY not found in environment variables (.env file).")
        return

    try:
        # Initialize the client exactly as in llm_translator.py
        aclient = AsyncOpenAI(
            base_url=GROQ_BASE_URL,
            api_key=groq_api_key
        )

        # Define a simple test prompt
        test_messages = [{"role": "user", "content": "Say exactly 'Hello Groq Test'"}]

        # Make the API call with a timeout
        response = await asyncio.wait_for(
            aclient.chat.completions.create(
                model=TEST_MODEL,
                messages=test_messages,
                temperature=0.1,
                max_tokens=50 # Keep response short
            ),
            timeout=60.0 # Use a reasonable timeout (e.g., 60 seconds)
        )

        print("\n--- Groq API Call Successful ---")
        print("Response:")
        print(response.choices[0].message.content)

    except asyncio.TimeoutError:
        print("\n--- Groq API Call FAILED ---")
        print("Error: The API call timed out after 60 seconds.")
        print("Possible reasons: Network issue, Firewall block, Groq service slow/down.")
    except OpenAIError as api_err: # Catch specific OpenAI client errors
        print("\n--- Groq API Call FAILED ---")
        print(f"Error: API Error occurred: {api_err}")
        print(f"Status Code: {api_err.status_code}")
        print(f"Response Body: {api_err.body}")
        print("Possible reasons: Invalid API Key, Quota exceeded, Invalid request.")
    except Exception as e:
        print("\n--- Groq API Call FAILED ---")
        print(f"Error: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Running standalone Groq API test...")
    asyncio.run(test_api())
    print("\nTest finished.")