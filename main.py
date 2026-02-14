
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import PlainTextResponse
import hashlib
import hmac
import json
import requests
from datetime import datetime

app = FastAPI()

# --------------------------
# Configuration
# --------------------------
VERIFY_TOKEN ="verify_token"       # Your webhook verify token
APP_SECRET ="a9567d1b077a793273817ce095d910b0"         # For validating Meta webhook signature
ACCESS_TOKEN ="EAAcaF5VBMr4BQj8QJZCZBz5R2XsVAOi6oCNe29Qq7ySzb2SZCd0JvjQgqza2OxwfM04g2VjW9St60a8vWCzHphR1vMjr8PmYgAo0uUCiPCHfM1b8ZCnuuL6TZCoXPyEZBaF63hzMqeihm90cSkLeRIZCBBpaz0Cb4qf4Nbyszp88ZCjgHIPl3HUssRmk24fImDdVnAZDZD"
PHONE_NUMBER_ID=957359154126835
BUSINESS_NUMBER="919201962703"
# --------------------------

# --------------------------
# Webhook verification (GET)
# --------------------------
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print(" Webhook verified successfully!")
        return PlainTextResponse(content=challenge, status_code=200)

    raise HTTPException(status_code=403, detail="Verification failed")


# --------------------------
# Webhook POST (incoming messages)
# --------------------------
# @app.post("/webhook")
# async def receive_webhook(request: Request, x_hub_signature_256: str = Header(None)):
#     body = await request.body()

    # --- Signature validation ---
    # if not x_hub_signature_256:
    #     raise HTTPException(status_code=403, detail="Missing signature")

    # try:
    #     received_signature = x_hub_signature_256.split("=")[1]
    # except Exception:
    #     raise HTTPException(status_code=403, detail="Invalid signature format")

    # expected_signature = hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    # if not hmac.compare_digest(expected_signature, received_signature):
    #     raise HTTPException(status_code=403, detail="Invalid signature")


@app.post("/webhook")
async def receive_webhook(
    request: Request,
    authorization: str = Header(None)
):
    # # --- Token validation ---
    # if not authorization:
    #     raise HTTPException(status_code=403, detail="Missing Authorization header")

    # try:
    #     scheme, token = authorization.split(" ")
    # except ValueError:
    #     raise HTTPException(status_code=403, detail="Invalid Authorization format")

    # if scheme.lower() != "bearer" or token != VERIFY_TOKEN:
    #     raise HTTPException(status_code=403, detail="Invalid token")

    # --- Read body ---
    payload = await request.json()

    try:
        entry = payload.get("entry", [])[0]
        change = entry.get("changes", [])[0]
        value = change.get("value", {})

        metadata = value.get("metadata", {})
        phone_number_id = metadata.get("phone_number_id")

        contacts = value.get("contacts", [])
        contact = contacts[0] if contacts else {}
        profile_name = contact.get("profile", {}).get("name", "Unknown")

        messages = value.get("messages")

        if messages:
            message = messages[0]
            wa_id = message.get("from")
            message_type = message.get("type")
            timestamp = int(message.get("timestamp", 0))
            readable_time = (
                datetime.fromtimestamp(timestamp)
                if timestamp else "Unknown"
            )

            if message_type == "text":
                text_body = message.get("text", {}).get("body")
            else:
                text_body = f"[{message_type}]"

            print("\n==============================")
            print(" NEW WHATSAPP MESSAGE")
            print("==============================")
            print(f" Name     : {profile_name}")
            print(f" Number   : {wa_id}")
            print(f" Time     : {readable_time}")
            print(f" Type     : {message_type}")
            print(f" Message  : {text_body}")
            print("==============================\n")

    except Exception as e:
        print("Error processing webhook:", str(e))

    return {"status": "EVENT_RECEIVED"}


    payload = json.loads(body)

    # --- Process each entry/change ---
    try:
        entry = payload.get("entry", [])[0]
        change = entry.get("changes", [])[0]
        value = change.get("value", {})

        metadata = value.get("metadata", {})
        phone_number_id = metadata.get("phone_number_id")

        contacts = value.get("contacts", [])
        contact = contacts[0] if contacts else {}
        profile_name = contact.get("profile", {}).get("name", "Unknown")

        messages = value.get("messages")
        if messages:
            message = messages[0]
            wa_id = message.get("from")  # User number
            message_type = message.get("type")
            timestamp = int(message.get("timestamp", 0))
            readable_time = datetime.fromtimestamp(timestamp) if timestamp else "Unknown"

            # --- Prepare message content ---
            if message_type == "text":
                text_body = message.get("text", {}).get("body")
            elif message_type in ["image", "video", "audio", "document"]:
                media = message.get(message_type, {})
                text_body = f"[{message_type} message, ID: {media.get('id')}]"
            else:
                text_body = f"[Unknown type: {message_type}]"

            # --- Print nicely ---
            print("\n==============================")
            print(" NEW WHATSAPP MESSAGE")
            print("==============================")
            print(f" Name     : {profile_name}")
            print(f" Number   : {wa_id}")
            print(f" Time     : {readable_time}")
            print(f" Type     : {message_type}")
            print(f" Message  : {text_body}")
            print("==============================\n")

            # --- Auto-reply safely ---
            if wa_id and phone_number_id and wa_id != BUSINESS_NUMBER:
                send_reply(phone_number_id, wa_id, "Hello from Khushi")
            else:
                print("ℹ️ Message from business number itself. Skipping reply.")

        else:
            print("ℹ️ No user message in this webhook event. Skipping reply.")

    except Exception as e:
        print("⚠️ Error processing webhook:", str(e))

    return {"status": "EVENT_RECEIVED"}


# --------------------------
# Function to send WhatsApp reply
# --------------------------
def send_reply(phone_number_id, to_number, message):
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"✅ Replied to {to_number} with: {message}")
    else:
        print(f"❌ Failed to reply: {response.status_code} {response.text}")
