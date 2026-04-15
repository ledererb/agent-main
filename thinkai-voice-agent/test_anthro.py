import asyncio
import os
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv("C:/Users/dani pc xd/Desktop/agent-main/thinkai-voice-agent/.env")

async def main():
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    models = ["claude-3-5-sonnet-20240620", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
    for m in models:
        try:
            resp = await client.messages.create(
                model=m,
                max_tokens=10,
                messages=[{"role":"user", "content":"hello"}]
            )
            print(f"{m} SUCCESS")
        except Exception as e:
            print(f"{m} FAIL: {e}")

asyncio.run(main())
