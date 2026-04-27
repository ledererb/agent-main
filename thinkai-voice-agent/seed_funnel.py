import database as db
from loguru import logger
import json

def seed():
    clients = db.get_clients()
    logger.info(f"Talált kliensek száma: {len(clients)}")
    
    for c in clients:
        status = c.get("status", "uj")
        custom_data_str = c.get("custom_data", "{}")
        if isinstance(custom_data_str, dict):
            custom_data = custom_data_str
        else:
            try:
                custom_data = json.loads(custom_data_str)
            except Exception:
                custom_data = {}
        
        name = custom_data.get("name", "Ismeretlen")
        
        # Státusz térképezése
        stage = "relevant"
        if status == "kapcsolatfelvetel":
            stage = "valaszolt"
        elif status == "targyalas":
            stage = "ajanlat"
        elif status == "szerzodott":
            stage = "foglalt"
            
        logger.info(f"Ügyfél '{name}' -> funnel_stage: {stage}")
        
        db.log_interaction(
            type="system_seed",
            topic="Retroaktív tölcsér adat",
            summary=f"Kliens (ID: {c.get('id')}) importálva Kanban státusz alapján: {status}",
            result="Sikeres betöltés",
            tool_name="seed_script",
            session_id="",
            funnel_stage=stage
        )
        
    # Extra, hogy szebb legyen a diagram: hozzáadunk pár "múltbeli" fantom interakciót,
    # hogy meglegyen a "leszakadó" tölcsér forma az összes_releváns és válaszolt között.
    logger.info("Fantom érdeklődők hozzáadása a diagram látványossága érdekében...")
    for i in range(15):
        db.log_interaction(
            type="email",
            topic="Generált releváns megkeresés",
            summary="Rendszer által generált teszt adat a tölcsérhez",
            result="Válaszra vár",
            tool_name="seed_script",
            session_id="",
            funnel_stage="relevant"
        )
    for i in range(8):
        db.log_interaction(
            type="messenger",
            topic="Generált válaszolt megkeresés",
            summary="Rendszer által generált teszt adat a tölcsérhez",
            result="Válasz elküldve",
            tool_name="seed_script",
            session_id="",
            funnel_stage="valaszolt"
        )
        
    for i in range(4):
        db.log_interaction(
            type="phone",
            topic="Generált ajánlat fázis",
            summary="Rendszer által generált teszt adat a tölcsérhez",
            result="Ajánlat elküldve",
            tool_name="seed_script",
            session_id="",
            funnel_stage="ajanlat"
        )

    logger.info("Kész! A tölcsér most már látható értékekkel fog betölteni.")

if __name__ == "__main__":
    seed()
