-- Supabase Seed Data for ThinkAI Voice Agent

-- Kanban columns
INSERT INTO kanban_columns (id, name, order_index) VALUES 
('uj', 'Új', 1),
('kapcsolatfelvetel', 'Kapcsolatfelvétel', 2),
('targyalas', 'Tárgyalás', 3),
('szerzodott', 'Szerződött', 4)
ON CONFLICT (id) DO NOTHING;

-- Client fields
INSERT INTO client_fields (id, name, order_index) VALUES 
('name', 'Név', 1),
('email', 'Email', 2),
('phone', 'Telefonszám', 3),
('beszelgetes_naplo', 'Beszélgetés napló', 4)
ON CONFLICT (id) DO NOTHING;

-- Test clients
INSERT INTO clients (name, email, phone, status, custom_data) VALUES 
('Teszt Elek', 'teszt@elek.hu', '+36301234567', 'uj', '{"name": "Teszt Elek", "email": "teszt@elek.hu", "phone": "+36301234567", "beszelgetes_naplo": "[2026-04-27 12:00] Ügyfél regisztrált"}'::jsonb)
ON CONFLICT DO NOTHING;
