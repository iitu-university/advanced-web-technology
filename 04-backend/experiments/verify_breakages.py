"""Reproduce all eight Lab 7 failures in temporary source copies and a disposable DB.

Run from the backend root. LAB7_EXPERIMENT_DATABASE_URL must name a database
ending in _experiments. Its catalog is reset; the application source is untouched.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ["LAB7_EXPERIMENT_DATABASE_URL"]
assert make_url(URL).database.endswith("_experiments"), "Use a disposable *_experiments database"
ENV = {**os.environ, "DATABASE_URL": URL, "SQL_ECHO": "false", "PYTHONDONTWRITEBYTECODE": "1"}
LOG = []
REPORT = {"checked_at": datetime.now(timezone.utc).isoformat(), "experiments": []}


def run(folder, *args, expected=0, contains=None):
    result = subprocess.run([sys.executable, *args], cwd=folder, env=ENV, text=True, capture_output=True)
    output = result.stdout + result.stderr
    LOG.append('$ python ' + ' '.join(args) + '\n' + output + f'Exit: {result.returncode}\n')
    assert result.returncode == expected, output
    if contains:
        assert contains in output, output
    return output


def change(folder, file, old, new):
    path = folder / file
    source = path.read_text()
    assert old in source, (file, old)
    path.write_text(source.replace(old, new))


def copy_project(parent, name):
    folder = parent / name
    shutil.copytree(ROOT, folder, ignore=shutil.ignore_patterns('.venv', '.env', '__pycache__', 'verification', '.git'))
    return folder


def note(number, title, observation):
    REPORT['experiments'].append({'number': number, 'title': title, 'observation': observation})
    print(f'PASS {number}: {title}')


def api_error(folder, path, body, error_class):
    code = f'''
import traceback
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from main import app
with TestClient(app, raise_server_exceptions=False) as client:
    response = client.post({path!r}, json={body!r})
    print(response.status_code, response.text)
    assert response.status_code == 500
try:
    with TestClient(app) as client:
        client.post({path!r}, json={body!r})
except IntegrityError as exc:
    print(type(exc.orig).__name__, exc.orig.diag.constraint_name)
    assert type(exc.orig).__name__ == {error_class!r}
    traceback.print_exc()
else:
    raise AssertionError('Expected IntegrityError')
'''
    return run(folder, '-c', code, contains=error_class)


def main():
    with tempfile.TemporaryDirectory(prefix='lab7-breakages-') as tmp:
        parent = Path(tmp)
        clean = copy_project(parent, 'clean')
        run(clean, '-m', 'alembic', 'upgrade', 'head')
        with psycopg.connect(URL.replace('postgresql+psycopg://', 'postgresql://'), autocommit=True) as conn:
            conn.execute((ROOT / 'seed.sql').read_text())

            folder = copy_project(parent, '01-names')
            change(folder, 'db.py', '"uq": "%(table_name)s_%(column_0_N_name)s_key"', '"uq": "%(table_name)s_%(column_0_name)s_unique"')
            run(folder, 'check_models.py', expected=1, contains='students_email_unique')
            note(1, 'changed naming convention', 'students_email_unique/enrollments_course_id_unique differ from the database')

            folder = copy_project(parent, '02-validation')
            change(folder, 'schemas.py', 'name: str = Field(min_length=2)', 'name: str')
            api_error(folder, '/students', {'name': 'N', 'email': 'n@example.com'}, 'CheckViolation')
            note(2, 'removed Pydantic min_length', 'HTTP 500; students_name_check rejected the row')

            folder = copy_project(parent, '03-dictionary')
            change(folder, 'main.py', '"students_email_key":', '"students_email_uniq":')
            api_error(folder, '/students', {'name': 'Aigerim Two', 'email': 'aigerim@example.com'}, 'UniqueViolation')
            note(3, 'misspelled constraint dictionary key', 'HTTP 500; actual name is students_email_key')

            try:
                conn.execute('ALTER TABLE courses ALTER COLUMN title DROP NOT NULL')
                run(clean, '-m', 'alembic', 'check', expected=255, contains='modify_nullable')
                conn.execute('ALTER TABLE courses ALTER COLUMN title SET NOT NULL')
                conn.execute('ALTER TABLE courses ALTER COLUMN title TYPE varchar(100)')
                run(clean, '-m', 'alembic', 'check', expected=255, contains='modify_type')
            finally:
                conn.execute('ALTER TABLE courses ALTER COLUMN title SET NOT NULL')
                conn.execute('ALTER TABLE courses ALTER COLUMN title TYPE text')
            run(clean, '-m', 'alembic', 'check', contains='No new upgrade operations')
            note(4, 'database title nullability and type drift', 'alembic check: modify_nullable, then modify_type; clean after restoration')

            folder = copy_project(parent, '05-not-null')
            run(folder, '-m', 'alembic', 'downgrade', '-1')
            migration = folder / 'alembic/versions/0002_add_course_level.py'
            source = migration.read_text()
            start = source.index('def upgrade()')
            end = source.index('def downgrade()')
            migration.write_text(source[:start] + "def upgrade() -> None:\n    op.add_column('courses', sa.Column('level', sa.Text(), nullable=False))\n\n\n" + source[end:])
            run(folder, '-m', 'alembic', 'upgrade', 'head', expected=1, contains='NotNullViolation')
            run(folder, '-m', 'alembic', 'current', contains='0001')
            migration.write_text(source)
            run(folder, '-m', 'alembic', 'upgrade', 'head')
            run(folder, '-m', 'alembic', 'check', contains='No new upgrade operations')
            note(5, 'naive required column on existing rows', 'NotNullViolation; revision stayed 0001; three-step migration succeeded')

            folder = copy_project(parent, '06-missing-import')
            change(folder, 'alembic/env.py', 'import models  #', '# import models  #')
            run(folder, '-m', 'alembic', 'revision', '--autogenerate', '-m', 'oops', '--rev-id', '0003')
            draft = (folder / 'alembic/versions/0003_oops.py').read_text()
            assert all(f"op.drop_table('{table}')" in draft for table in ('courses', 'students', 'enrollments'))
            LOG.append('Generated draft (never applied):\n' + draft)
            note(6, 'removed import models', 'empty metadata proposed dropping all three tables; draft was never applied')

            folder = copy_project(parent, '07-missing-migration')
            change(folder, 'models.py', 'email: Mapped[str] = mapped_column(unique=True)', 'email: Mapped[str] = mapped_column(unique=True)\n    phone: Mapped[str | None]')
            run(folder, '-m', 'alembic', 'check', expected=255, contains='students.phone')
            note(7, 'added model phone without migration', 'alembic check reported added column students.phone')

            folder = copy_project(parent, '08-heads')
            run(folder, '-m', 'alembic', 'revision', '-m', 'add student phone', '--rev-id', '0003')
            run(folder, '-m', 'alembic', 'revision', '-m', 'add course language', '--rev-id', '0004', '--head', '0002', '--splice')
            heads = run(folder, '-m', 'alembic', 'heads')
            assert '0003 (head)' in heads and '0004 (head)' in heads
            run(folder, '-m', 'alembic', 'upgrade', 'head', expected=255, contains='Multiple head revisions')
            run(folder, '-m', 'alembic', 'merge', 'heads', '-m', 'merge phone and language', '--rev-id', '0005')
            run(folder, '-m', 'alembic', 'heads', contains='0005 (head)')
            run(folder, '-m', 'alembic', 'history', contains='mergepoint')
            note(8, 'two migration heads', 'upgrade head refused; a merge revision with parents 0003 and 0004 produced one head')

            REPORT['count_trap'] = conn.execute('SELECT c.id, count(*) AS wrong, count(e.id) AS enrolled FROM courses c LEFT JOIN enrollments e ON e.course_id=c.id GROUP BY c.id ORDER BY c.id').fetchall()
            conn.execute((ROOT / 'seed.sql').read_text())
            REPORT['final_counts'] = list(conn.execute('SELECT (SELECT count(*) FROM courses), (SELECT count(*) FROM students), (SELECT count(*) FROM enrollments)').fetchone())
            assert REPORT['final_counts'] == [6, 3, 6]
        run(clean, '-m', 'alembic', 'heads', contains='0002 (head)')
        run(clean, '-m', 'alembic', 'check', contains='No new upgrade operations')
        assert len(list((ROOT / 'alembic/versions').glob('*.py'))) == 2
    output = ROOT / 'verification'
    output.mkdir(exist_ok=True)
    (output / 'breakages.log').write_text('\n'.join(LOG))
    (output / 'breakages.json').write_text(json.dumps(REPORT, indent=2) + '\n')
    print('8 of 8 experiments reproduced; source and final migration history restored')


if __name__ == '__main__':
    main()
