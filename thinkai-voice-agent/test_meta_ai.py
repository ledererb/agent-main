import asyncio
import os
from dotenv import load_dotenv

# Ensure env vars are loaded
load_dotenv(".env")
os.environ["META_PAGE_ACCESS_TOKEN"] = "mock_token"  # mock so it doesn't try actual send unless we have one

from web_server import process_meta_message

async def run_test():
    sender_id = "test_user_777"
    message = "Szia! Kovács Béla vagyok. A 3-as BMWm-be szeretnék egy olajcserét kérni holnap délelőttre, a telefonszámom 06301234567."
    print("Testing processing for message:", message)
    
    await process_meta_message(sender_id, message)
    print("Processing finished.")

if __name__ == "__main__":
    asyncio.run(run_test())
