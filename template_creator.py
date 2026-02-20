import os
import re
import asyncio
import httpx
import google.generativeai as genai
from dotenv import load_dotenv


# ==============================
# Load Environment Variables
# ==============================
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
WABA_ID = os.getenv("WABA_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TEMPLATE_LANGUAGE = os.getenv("TEMPLATE_LANGUAGE", "en_US")
META_API_VERSION = os.getenv("META_API_VERSION", "v19.0")

if not all([ACCESS_TOKEN, WABA_ID, GEMINI_API_KEY]):
    raise ValueError("❌ Missing required environment variables in .env")


# ==============================
# Configure Gemini 2.5 Pro
# ==============================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")


# ==============================
# Utility: Clean Template Name
# ==============================
def clean_template_name(name: str):
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9_]", "_", name)
    return name


# ==============================
# Step 1: Generate Template
# ==============================
async def generate_template(prompt: str):
    ai_prompt = f"""
    Create a professional WhatsApp Business message template.

    Rules:
    - Under 500 characters
    - No spammy words
    - No exaggerated claims
    - No excessive emojis
    - Professional & engaging
    - If personalization needed, use {{1}}

    User Idea:
    {prompt}

    Return ONLY the final template message text.
    """

    try:
        response = model.generate_content(ai_prompt)
        if not response.text:
            raise Exception("Empty response from Gemini")

        return response.text.strip()

    except Exception as e:
        raise Exception(f"Gemini Error: {str(e)}")


# ==============================
# Step 2: Submit Template to Meta
# ==============================
async def submit_template(name: str, category: str, body_text: str):

    url = f"https://graph.facebook.com/{META_API_VERSION}/{WABA_ID}/message_templates"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": clean_template_name(name),
        "language": TEMPLATE_LANGUAGE,
        "category": category,
        "components": [
            {
                "type": "BODY",
                "text": body_text
            }
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)

    return response.status_code, response.text


# ==============================
# Main CLI Execution
# ==============================
async def main():

    print("\n WhatsApp Template Creator\n")

    template_name = input("Enter Template Name: ").strip()
    prompt = input("Enter Simple Idea Prompt: ").strip()

    category = input(
        "Enter Category (MARKETING / UTILITY / AUTHENTICATION) [Default: MARKETING]: "
    ).strip().upper()

    # Default category
    if not category:
        category = "MARKETING"

    allowed_categories = ["MARKETING", "UTILITY", "AUTHENTICATION"]

    if category not in allowed_categories:
        print(" Invalid category. Using MARKETING.")
        category = "MARKETING"

    print(f"\n Final Category: {category}")
    print("\n Generating template using Gemini 2.5 Pro...\n")

    try:
        generated_message = await generate_template(prompt)

        print(" Generated Template:\n")
        print("----------------------------------------")
        print(generated_message)
        print("----------------------------------------")

        print("\n Submitting to Meta for approval...\n")

        status_code, response_text = await submit_template(
            template_name,
            category,
            generated_message
        )

        print(f" Meta Response Status: {status_code}")
        print(" Response:")
        print(response_text)

        if status_code == 200:
            print("\n Template submitted successfully!")
        else:
            print("\n Submission failed. Check error above.")

    except Exception as e:
        print(f"\n Error: {str(e)}")


# ==============================
# Run Program
# ==============================
if __name__ == "__main__":
    asyncio.run(main())
