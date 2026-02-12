import os
import base64
from gemini_webapi import GeminiClient
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

SECURE_1PSID = os.getenv("SECURE_1PSID")
SECURE_1PSIDTS = os.getenv("SECURE_1PSIDTS")

async def get_gemini_client():
    if not SECURE_1PSID or not SECURE_1PSIDTS:
        raise HTTPException(status_code=500, detail="Server Error: Missing Gemini Cookies in environment variables.")
    
    client = GeminiClient(SECURE_1PSID, SECURE_1PSIDTS)
    # Initialize client (adjust timeout/auto_close as needed)
    await client.init(timeout=30, auto_close=False, auto_refresh=True)
    return client

async def generate_response(prompt_text: str, image_data: bytes = None):
    client = await get_gemini_client()
    if image_data:
        response = await client.generate_content(prompt_text, image=image_data)
    else:
        response = await client.generate_content(prompt_text)
    return response.text

async def process_gemini_request(contents):
    prompt_text = ""
    image_data = None
    
    
    for content in contents:
        for part in content.parts:
            # Handle Text
            if part.text:
                prompt_text += part.text + "\n"
            
            # Handle Image (Base64)
            if part.inline_data:
                try:
                    image_data = base64.b64decode(part.inline_data.data)
                except Exception:
                    print("Failed to decode base64 image")

    return await generate_response(prompt_text, image_data)