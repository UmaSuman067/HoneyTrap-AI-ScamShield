from __future__ import annotations
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    sender: str
    text: str
    timestamp: Optional[str] = None

class Metadata(BaseModel):
    channel: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None

class HoneyPotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Dict] = Field(default_factory=list)
    metadata: Optional[Metadata] = None

class Intelligence(BaseModel):
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)

class AgentResponse(BaseModel):
    status: str
    reply: str
    extracted_intelligence: Intelligence