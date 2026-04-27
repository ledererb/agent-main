import sqlite3
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger
from datetime import datetime, timezone

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

db_path = "thinkai.db"

def migrate_table(conn, table_name, columns, json_columns=None, id_col=None):
    logger.info(f"Migrating table: {table_name}")
    try:
        rows = conn.execute(f"SELECT * FROM {table_name}" + (f" ORDER BY {id_col} ASC" if id_col else "")).fetchall()
        
        # Batch insert
        records = []
        for r in rows:
            record = {}
            for col in columns:
                val = r[col]
                # convert json strings
                if json_columns and col in json_columns and val:
                    try:
                        val = json.loads(val)
                    except Exception:
                        pass
                if isinstance(val, str):
                    if val == "":
                        val = None
                    elif len(val) == 19 and val[10] in ("T", " "):
                        try:
                            dt = datetime.fromisoformat(val.replace(" ", "T"))
                            if dt.tzinfo is None:
                                val = dt.replace(tzinfo=timezone.utc).isoformat()
                        except Exception:
                            pass
                        
                record[col] = val
            records.append(record)
        
        if records:
            # We insert in batches of 100
            for i in range(0, len(records), 100):
                batch = records[i:i+100]
                try:
                    supabase.table(table_name).upsert(batch).execute()
                except Exception as e:
                    logger.warning(f"Error inserting batch into {table_name}: {e}")
            logger.info(f"Inserted {len(records)} records into {table_name}.")
        else:
            logger.info(f"No records to migrate for {table_name}.")
    except Exception as e:
        logger.error(f"Error migrating {table_name}: {e}")

def main():
    if not os.path.exists(db_path):
        logger.error(f"SQLite DB not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Text PK tables
    # migrate_table(conn, "kanban_columns", ["id", "name", "order_index"])
    # migrate_table(conn, "client_fields", ["id", "name", "order_index"])
    
    # Auto-increment tables (we omit the 'id' column so Supabase generates new ones, or we can keep them with upsert. 
    # Using upsert requires the ID. We can try with ID to preserve them, but sequences won't update.
    # Since we can't easily update sequence from REST, let's omit ID so it generates new ones.)
    
    # migrate_table(conn, "admin_users", ["username", "email", "password_hash", "created_at"], id_col="id")
    # migrate_table(conn, "sessions", ["session_id", "room_name", "started_at", "ended_at", "duration_seconds", "participant"], id_col="id")
    # migrate_table(conn, "interactions", ["session_id", "type", "topic", "summary", "result", "tool_name", "created_at"], id_col="id")
    migrate_table(conn, "calendar_events", ["title", "start_dt", "end_dt", "duration_minutes", "attendee", "attendee_email", "created_at"], id_col="id")
    # migrate_table(conn, "email_logs", ["to_name", "to_email", "subject", "message", "sent_at", "status", "error", "session_id"], id_col="id")
    # migrate_table(conn, "tasks", ["text", "priority", "due_date", "created_at", "completed", "session_id"], id_col="id")
    # migrate_table(conn, "clients", ["name", "email", "phone", "status", "custom_data", "created_at"], json_columns=["custom_data"], id_col="id")

    logger.info("Migration complete!")

if __name__ == "__main__":
    main()
