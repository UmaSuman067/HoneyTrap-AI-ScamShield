from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

import os, re, json, asyncio, requests
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
from typing import List, Optional

app = FastAPI()

# ================== CONFIGURATION ==================
GEMINI_API_KEY = "AIzaSyAa8r7oL2DxNzD_2QZRR4PUPh0gppRGRHg" 
VALID_API_KEY = "sk_test_guvi_2026"
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

scam_history = []
_sse_clients = []

# ================== MODELS ==================

class MessageDetail(BaseModel):
    sender: str
    text: str
    timestamp: Optional[str] = None

class HoneyPotRequest(BaseModel):
    sessionId: str
    message: MessageDetail
    conversationHistory: List[MessageDetail] = []
    metadata: Optional[dict] = {"channel": "SMS", "language": "English", "locale": "IN"}

# ================== INTELLIGENCE EXTRACTION ==================

def extract_intelligence(text: str):
    return {
        "bankAccounts": re.findall(r"\b\d{9,18}\b", text),
        "upiIds": re.findall(r"[a-zA-Z0-9.\-_]+@[a-zA-Z]+", text),
        "phishingLinks": re.findall(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", text),
        "phoneNumbers": re.findall(r"\+?\d{10,12}", text),
        "suspiciousKeywords": [w for w in ["blocked", "urgent", "verify", "suspend", "kyc"] if w in text.lower()]
    }

# ================== ROUTES ==================

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/honey-pot")
async def handle_message(request: HoneyPotRequest, x_api_key: str = Header(None)):
    if x_api_key != VALID_API_KEY: 
        raise HTTPException(status_code=403, detail="Invalid API Key")

    scammer_text = request.message.text
    session_id = request.sessionId
    intel = extract_intelligence(scammer_text)
    
    # AI Persona Engagement with History
    history_str = "\n".join([f"{m.sender}: {m.text}" for m in request.conversationHistory])
    prompt = f"Persona: Priya (confused victim). Context:\n{history_str}\nScammer: {scammer_text}\nPriya's Response:"

    try:
        resp = model.generate_content(prompt)
        ai_reply = resp.text
    except:
        ai_reply = "Oh no, I'm so worried. What should I do?"

    # GUVI Mandatory Callback
    total_msgs = len(request.conversationHistory) + 1
    callback_payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": total_msgs,
        "extractedIntelligence": intel,
        "agentNotes": f"Detected {request.metadata.get('channel')} scam."
    }
    try:
        requests.post(GUVI_CALLBACK_URL, json=callback_payload, timeout=5)
    except:
        pass

    # Broadcast to Dashboard
    event = {
        "sessionId": session_id,
        "message": scammer_text,
        "ai_reply": ai_reply,
        "intel": intel,
        "medium": request.metadata.get("channel", "SMS")
    }
    scam_history.append(event)
    for q in _sse_clients: await q.put(event)

    return {"status": "success", "reply": ai_reply}

@app.get("/history")
async def get_history(): return scam_history

@app.get("/events")
async def sse(request: Request):
    q = asyncio.Queue(); _sse_clients.append(q)
    async def stream():
        while True:
            if await request.is_disconnected(): break
            yield f"data: {json.dumps(await q.get())}\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream")