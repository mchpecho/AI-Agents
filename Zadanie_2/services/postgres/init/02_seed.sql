INSERT INTO machines(machine_id, model)
VALUES ('LNK-01', 'Lankovačka-MVP')
ON CONFLICT (machine_id) DO UPDATE SET model=EXCLUDED.model;
