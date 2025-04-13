# extractor.py
import json
import logging
from llm_translator import aclient 

logger = logging.getLogger(__name__)

EXTRACT_SYSTEM_PROMPT = """
You are an AI assistant tasked with extracting specific information from text content found on a web page.
You will be given:
1. An extraction query specifying what information to find.
2. The visible text content scraped from the web page screen.

Based *only* on the provided text content, extract the information requested in the query.
Structure your response as a JSON object containing the extracted data.
If the requested information is not found in the provided text, return an empty JSON object or indicate that the information is missing.
Do not invent information not present in the text.
Focus solely on the extraction task based on the text provided.
"""

# --- Extraction Method 1: LLM based on Visible Text ---
async def extract_data_from_text(query: str, visible_text: str | None) -> dict:
    """
    Uses an LLM to extract structured data based on a query from visible text content.
    """
    if not visible_text:
        logger.warning("Extraction called with no visible text provided.")
        return {"error": "No visible text content available for extraction."}
    if not aclient:
        logger.error("LLM client not available for extraction.")
        return {"error": "LLM client not initialized."}

    logger.info(f"Attempting extraction for query: '{query}'")
    # logger.debug(f"Visible text for extraction:\n{visible_text[:500]}...") # Log snippet

    messages = [
        {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Extraction Query: \"{query}\"\n\nVisible Text Content:\n```\n{visible_text}\n```"}
    ]

    try:
        response = await aclient.chat.completions.create(
            model="llama3-70b-8192", # Or another suitable model
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0, # Deterministic extraction
        )

        extracted_json_str = response.choices[0].message.content
        logger.info(f"LLM Extraction Response: {extracted_json_str}")
        extracted_data = json.loads(extracted_json_str)
        return extracted_data

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing LLM JSON response during extraction: {e}\nResponse: {extracted_json_str}")
        return {"error": f"Failed to parse extraction JSON: {e}", "raw_response": extracted_json_str}
    except Exception as e:
        logger.error(f"Error during LLM extraction: {e}")
        return {"error": f"LLM extraction failed: {e}"}

# --- Extraction Method 2: Vision Model (Optional - More Advanced) ---
async def extract_data_with_vision(query: str, screenshot_base64: str | None) -> dict:
    """
    Uses a vision-capable LLM to extract structured data based on a query from a screenshot.
    (Requires a vision model like GPT-4o/Gemini and appropriate client setup)
    """
    if not screenshot_base64:
        logger.warning("Vision extraction called with no screenshot provided.")
        return {"error": "No screenshot available for vision extraction."}
    if not aclient: # Or your vision-specific client
        logger.error("LLM client not available for vision extraction.")
        return {"error": "LLM client not initialized."}

    logger.info(f"Attempting vision extraction for query: '{query}'")

    # Construct messages for a vision model
    messages = [
        {
            "role": "system",
            "content": "You are an AI assistant analyzing a web page screenshot. Extract the information requested in the user query and respond ONLY with a valid JSON object containing the extracted data. If the information is not visible, return an empty JSON object."
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Extraction Query: \"{query}\""},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{screenshot_base64}"},
                },
            ],
        }
    ]

    try:
        # Ensure you are using a model that supports vision input
        response = await aclient.chat.completions.create(
            model="gpt-4o", # Or another vision model like "gemini-pro-vision"
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=1000, # Adjust as needed
        )

        extracted_json_str = response.choices[0].message.content
        logger.info(f"LLM Vision Extraction Response: {extracted_json_str}")
        extracted_data = json.loads(extracted_json_str)
        return extracted_data

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing vision LLM JSON response: {e}\nResponse: {extracted_json_str}")
        return {"error": f"Failed to parse vision extraction JSON: {e}", "raw_response": extracted_json_str}
    except Exception as e:
        logger.error(f"Error during vision LLM extraction: {e}")
        return {"error": f"Vision LLM extraction failed: {e}"}

# --- Main Extraction Function ---
async def extract_data(query: str, state: dict) -> dict:
    """
    Extracts structured data based on the query and current state.
    Prioritizes vision extraction if screenshot is available and configured,
    otherwise falls back to text-based extraction.
    """
    screenshot_base64 = state.get("screenshot_base64")
    visible_text = state.get("visible_text")

    # --- Choose Extraction Strategy ---
    # Strategy 1: Use Vision Model if available (Generally more accurate for visual layout)
    # (Uncomment this block if you want to prioritize vision)
    if screenshot_base64:
        logger.info("Using vision-based extraction.")
        # Make sure your LLM client (aclient) and model support vision
        # return await extract_data_with_vision(query, screenshot_base64)
        pass # Comment this pass if using vision

    # Strategy 2: Use Text-Based Extraction (Fallback or default)
    if visible_text:
        logger.info("Using text-based extraction.")
        return await extract_data_from_text(query, visible_text)
    elif screenshot_base64:
         # Fallback to vision if text OCR failed but screenshot exists
         logger.info("No visible text from OCR, falling back to vision-based extraction.")
         # return await extract_data_with_vision(query, screenshot_base64)
         return {"error": "Visible text OCR failed, Vision extraction not implemented/enabled."} # Placeholder if vision is commented out

    # Strategy 3: No content available
    else:
        logger.error("No screenshot or visible text available for extraction.")
        return {"error": "No content available to extract from."}