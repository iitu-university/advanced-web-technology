BEGIN;

-- Running upgrade 0001 -> 0002

ALTER TABLE courses ADD COLUMN level TEXT;

UPDATE courses SET level = CASE WHEN is_elective THEN 'beginner' ELSE 'intermediate' END;

ALTER TABLE courses ALTER COLUMN level SET NOT NULL;

UPDATE alembic_version SET version_num='0002' WHERE alembic_version.version_num = '0001';

COMMIT;

