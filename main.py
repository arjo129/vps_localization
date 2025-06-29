from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import asyncio
import google.generativeai as genai
import os
from pydantic import BaseModel
import json

class ShopsSeen(BaseModel):
    shop_name: str

# Ensure you have the GOOGLE_API_KEY environment variable set
app = FastAPI()

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    # You can process the file here (e.g., save, analyze, etc.)
    contents = await file.read()
    # Forward the image contents to Gemini with a prompt template
    image_part = {
        "mime_type": file.content_type,
        "data": contents
    }

    # The google.generativeai (Gemini) API is synchronous as of now.
    # You cannot use async/await directly with it.
    # If you want to avoid blocking, run it in a thread pool:

    def call_gemini():
        model = genai.GenerativeModel('gemini-2.0-flash')
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        # Request Gemini to return structured JSON output
        response = model.generate_content(
            [
            {
                "role": "user",
                "parts": [
                {
                    "text": (
                    "List the names of the shops in the image as a JSON array of strings. "
                    )
                },
                image_part
                ]
            }
            ],
            generation_config={
            "response_mime_type": "application/json",
            "response_schema": list[ShopsSeen],
            }
        )
        # Parse the JSON output
        try:
            shop_list = json.loads(response.text)
        except Exception:
            shop_list = response.text
        return shop_list
        #return response.text

    gemini_result = await asyncio.to_thread(call_gemini)
    
    return JSONResponse({
        "list": gemini_result
    })

