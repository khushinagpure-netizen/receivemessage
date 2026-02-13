import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Get VERIFY_TOKEN from environment
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

app = FastAPI()

# ---------------------------
# Meta GET verification
# ---------------------------
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        return JSONResponse(content=int(challenge))
    else:
        print("❌ Webhook verification failed")
        return JSONResponse(content="Forbidden", status_code=403)


# ---------------------------
# Receive WhatsApp messages
# ---------------------------
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("📩 Received WhatsApp payload:")
    print(data)

    try:
        messages = data["entry"][0]["changes"][0]["value"].get("messages", [])
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
