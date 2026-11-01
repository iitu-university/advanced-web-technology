"""Real HTTP restart check. Run from backend root against a disposable *_live_test DB."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import psycopg
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ['DATABASE_URL']
assert make_url(URL).database.endswith('_live_test'), 'Use a disposable *_live_test database'
PORT = int(os.getenv('LIVE_TEST_PORT', '18000'))
BASE = f'http://127.0.0.1:{PORT}'
OUTPUT = ROOT / 'verification'
ENV = {**os.environ, 'SQL_ECHO': 'false'}


def seed():
    with psycopg.connect(URL.replace('postgresql+psycopg://', 'postgresql://'), autocommit=True) as conn:
        conn.execute((ROOT / 'seed.sql').read_text())


def start(log):
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', str(PORT)], cwd=ROOT, env=ENV, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError('API stopped before becoming ready')
        try:
            if httpx.get(BASE + '/', timeout=1).status_code == 200:
                return process
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    process.terminate()
    process.wait(timeout=5)
    raise RuntimeError('API did not become ready')


def main():
    OUTPUT.mkdir(exist_ok=True)
    result = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT, env=ENV, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    seed()
    report, process = {}, None
    with (OUTPUT / 'live-server.log').open('w') as log:
        try:
            process = start(log)
            with httpx.Client(base_url=BASE) as client:
                report['swagger_status'] = client.get('/docs').status_code
                report['operations'] = sum(len(v) for v in client.get('/openapi.json').json()['paths'].values())
                report['beginner_ids'] = [c['id'] for c in client.get('/courses?level=beginner').json()]
                assert report['beginner_ids'] == ['ai-integration', 'api-design']
                liked = client.post('/courses/web-security/like')
                assert liked.status_code == 200 and liked.json()['likes'] == 22
                student = client.post('/students', json={'name': 'Nurlan Abenov', 'email': 'nurlan@example.com'})
                assert student.status_code == 201
                enrollment = client.post('/enrollments', json={'courseId': 'web-security', 'studentId': student.json()['id']})
                assert enrollment.status_code == 201
                report['enrollment_before_restart'] = enrollment.json()
                report['first_pid'] = process.pid
            process.terminate()
            process.wait(timeout=10)
            process = start(log)
            report['second_pid'] = process.pid
            assert report['first_pid'] != report['second_pid']
            with httpx.Client(base_url=BASE) as client:
                report['likes_after_restart'] = client.get('/courses/web-security').json()['likes']
                rows = client.get('/enrollments').json()
                report['enrollments_after_restart'] = len(rows)
                found = next(row for row in rows if row['id'] == enrollment.json()['id'])
                assert all(found[k] == v for k, v in enrollment.json().items())
                assert found['studentName'] == 'Nurlan Abenov'
                assert report['likes_after_restart'] == 22 and len(rows) == 7
                assert sum(s['enrolled'] for s in client.get('/stats/courses').json()) == len(rows)
            errors = subprocess.run([sys.executable, 'try_errors.py'], cwd=ROOT, env={**ENV, 'API_BASE_URL': BASE}, capture_output=True, text=True)
            (OUTPUT / 'try-errors.log').write_text(errors.stdout + errors.stderr)
            assert errors.returncode == 0 and '5 of 5 as expected' in errors.stdout
            report.update(error_check='5 of 5 as expected', passed=True)
        finally:
            if process:
                process.terminate()
                process.wait(timeout=10)
            seed()
    (OUTPUT / 'live-results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
