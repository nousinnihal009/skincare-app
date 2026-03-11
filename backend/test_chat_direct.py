import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

# We need to setup logging to see the logger.error output
logging.basicConfig(level=logging.INFO)

from app.services.chatbot import stream_chat_response

async def run():
    print("Starting chat stream...")
    try:
        async for chunk in stream_chat_response("test_user", "test_session", "Hello", None, None):
            print(chunk)
    except Exception as e:
        print(f"Exception escaped: {e}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())
