import os
import imaplib
from dotenv import load_dotenv

load_dotenv("C:/Users/dani pc xd/Desktop/agent-main/thinkai-voice-agent/.env")

server = os.getenv("IMAP_SERVER")
user = os.getenv("IMAP_USER")
pwd = os.getenv("IMAP_PASS")

mail = imaplib.IMAP4_SSL(server, 993)
mail.login(user, pwd)
mail.select("inbox")

# Find all seen messages from today
status, messages = mail.search(None, "SEEN")
if status == "OK" and messages[0]:
    msg_ids = messages[0].split()
    # take the last one
    last_msg = msg_ids[-1]
    mail.store(last_msg, "-FLAGS", "\\Seen")
    print(f"Set UNSEEN for msg {last_msg}")

mail.close()
mail.logout()
