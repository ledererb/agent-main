# -*- coding: utf-8 -*-
import database as db

def reseed():
    rules = db.get_triage_rules()
    for r in rules:
        db.delete_triage_rule(r['id'])
    
    defaults = [
        ('Általános információ', 'Normál', ''),
        ('Időpontkérés', 'Normál', ''),
        ('Árérdeklődés', 'Normál', ''),
        ('Panasz', 'Fontos', ''),
        ('Erős fájdalom', 'Sürgős', ''),
        ('Komplikáció', 'Sürgős', ''),
        ('Konfliktus', 'Kiemelt', 'vezeto@mintaklinika.hu')
    ]
    
    for s, p, e in defaults:
        db.add_triage_rule(s, p, e)
        
    print("Seeded successfully with UTF-8")

if __name__ == "__main__":
    reseed()
