import re

def main():
    try:
        # 1. Update database.py upsert_client
        with open('database.py', 'r', encoding='utf-8') as f:
            db_content = f.read()

        old_upsert = """        edit_client_details(existing["id"], curr_data)
        logger.info(f"Updated existing client (ID: {existing['id']})")"""
        new_upsert = """        edit_client_details(existing["id"], curr_data)
        update_client_status(existing["id"], status)
        logger.info(f"Updated existing client (ID: {existing['id']})")"""
        
        db_content = db_content.replace(old_upsert, new_upsert)
        
        with open('database.py', 'w', encoding='utf-8') as f:
            f.write(db_content)
        print("Updated database.py successfully!")

        # 2. Update email_processor.py to use session_id
        with open('email_processor.py', 'r', encoding='utf-8') as f:
            ep_content = f.read()

        # We need to insert session creation right before adding logs
        # old code:
        #         # Naplózás
        #         db.add_email_log(
        
        # let's find the logging block:
        old_logging = """        # Naplózás
        db.add_email_log(
            to_name=from_name,
            to_email=from_email,
            subject=f"Re: {subject}",
            message=email_reply,
            status="sent" if sent_ok else f"failed ({error_msg})",
            session_id=""
        )
        db.log_interaction(
            type="email",
            topic="Email AI válasz",
            summary=f"Bejövő e-mail {from_email} címről",
            result="Sikeres válasz" if sent_ok else "Hibás küldés",
            tool_name="imap_worker_ai",
            session_id=""
        )"""

        new_logging = """        # Naplózás
        session_id = f"email_{from_email}"
        db.create_session(session_id=session_id, room_name="Email Thread", participant=from_name)
        
        db.add_email_log(
            to_name=from_name,
            to_email=from_email,
            subject=f"Re: {subject}",
            message=email_reply,
            status="sent" if sent_ok else f"failed ({error_msg})",
            session_id=session_id
        )
        db.log_interaction(
            type="email",
            topic="Email AI válasz",
            summary=f"Bejövő e-mail {from_email} címről",
            result="Sikeres válasz" if sent_ok else "Hibás küldés",
            tool_name="imap_worker_ai",
            session_id=session_id
        )"""

        ep_content = ep_content.replace(old_logging, new_logging)
        
        with open('email_processor.py', 'w', encoding='utf-8') as f:
            f.write(ep_content)
            
        print("Updated email_processor.py successfully!")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
