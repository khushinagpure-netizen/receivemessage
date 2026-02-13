import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from dotenv import load_dotenv

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "12345")  # fallback if not set

app = FastAPI()

# ---------------------------
# Meta GET verification
# ---------------------------
@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Meta sends a GET request to verify the webhook.
    We respond with the hub.challenge if the VERIFY_TOKEN matches.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        return PlainTextResponse(challenge or "")  # return as plain text
    else:
        print("❌ Webhook verification failed")
        return PlainTextResponse("Forbidden", status_code=403)


# ---------------------------
# Receive WhatsApp messages
# ---------------------------
@app.post("/webhook")
async def receive_message(request: Request):
    """
    Handles incoming WhatsApp messages from Meta.
    Supports text, image, and document messages.
    """
    try:
        data = await request.json()
        print("📩 Received WhatsApp payload:")
        print(data)

        # Safely extract messages
        messages = (
            data.get("entry", [{}])[0]
                .get("changes", [{}])[0]
                .get("value", {})
                .get("messages", [])
        )

        for msg in messages:
            sender = msg.get("from")
            msg_type = msg.get("type")

            if msg_type == "text":
                text = msg.get("text", {}).get("body", "")
                print(f"📝 Message from {sender}: {text}")
            elif msg_type == "image":
                image_id = msg.get("image", {}).get("id")
                print(f"🖼 Image received from {sender}, media ID: {image_id}")
            elif msg_type == "document":
                doc_id = msg.get("document", {}).get("id")
                filename = msg.get("document", {}).get("filename")
                print(f"📄 Document from {sender}: {filename}, media ID: {doc_id}")
            else:
                print(f"⚠️ Received {msg_type} message from {sender}")

    except Exception as e:
        print("❌ Error parsing message:", e)

    return JSONResponse(content={"status": "received"})
