import os
import asyncio
from typing import List

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()

class LLMAdapter:
    def __init__(self):
        self.provider = LLM_PROVIDER
        if self.provider == "openai":
            import openai
            self._client = openai
            key = os.getenv("OPENAI_API_KEY")
            if key:
                self._client.api_key = key

    async def generate_reply(self, persona_prompt: str, conversation_history: List[str], latest_message: str) -> str:
        prompt = persona_prompt + "\n\nConversation History:\n" + "\n".join(conversation_history[-10:]) + f"\nScammer: {latest_message}\nPriya:"
        if self.provider == "openai":
            return await asyncio.to_thread(self._openai_chat, prompt)
        # Deterministic mock behavior that follows persona: worried, slightly confused, asks for payment details
        return (
            "Oh no, that sounds serious — I'm really worried! Where do I send the money? "
            "Can you give me your UPI ID so I can try from my brother's phone? "
            "Also, which account should I transfer to? I'm not very good with this."
        )

    def _openai_chat(self, prompt: str) -> str:
        # Minimal synchronous wrapper for older openai package usage
        r = self._client.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=200,
            temperature=0.6
        )
        return r.choices[0].text.strip()