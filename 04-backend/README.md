# Course Catalog API Lab 5

FastAPI serves six courses, updates like counters, and stores course enrollments in memory. It is the backend for the Next.js catalog in Lab 5. A process restart resets courses' likes and clears all enrollments; a page reload does not.

## Run

Python 3.10+ is required. Start this application before the frontend:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
fastapi dev main.py
```

Swagger: http://localhost:8000/docs. API: http://localhost:8000. Start the frontend on http://localhost:3000. In the course workspace this backend is `04-backend` and the frontend is `05-integration`; standalone repository names are `course-catalog-api` and `course-catalog`.

## What changed

CORS permits the exact origin `http://localhost:3000`, with no path or trailing slash, all methods and all headers. The permission is needed for browser requests to another origin; the Next.js server's requests do not use browser CORS rules. A foreign origin still gets a server response, but no `access-control-allow-origin` header. CORS does not prevent a simple POST from changing server state.

Models inherit `CamelModel`, with `alias_generator=to_camel`, `validate_by_name=True` and `validate_by_alias=True`. Python keeps snake_case; JSON and Swagger use `isElective`, `courseId` and `studentName`. Pydantic 2.11+ is explicit in `requirements.txt`. Both snake_case and aliases are accepted when validating models. Query parameters remain `is_elective`, `sort`, `q`, `page`, and `page_size`; Lab 4 filtering, search, sorting and pagination are preserved.

Three new operations complete the six documented routes:

| Method and route | Behavior |
| --- | --- |
| `GET /` | API running message |
| `GET /courses` | Six courses sorted by likes descending by default |
| `GET /courses/{course_id}` | One course, or 404 |
| `POST /courses/{course_id}/like` | Increment likes and return updated course, or 404 |
| `POST /enrollments` | Validate JSON, create enrollment and return 201 |
| `GET /enrollments` | Return current in-memory enrollment list |

Like example, starting from the original data:

```bash
curl -X POST http://localhost:8000/courses/web-security/like
```

```json
{"id":"web-security","title":"Web Security Essentials","description":"JWT/OAuth2, XSS, CSRF, and SQL injection defense.","credits":4,"isElective":false,"likes":22}
```

Enrollment example:

```bash
curl -X POST http://localhost:8000/enrollments -H 'Content-Type: application/json' -d '{"courseId":"web-security","studentName":"Aigerim"}'
```

```json
{"courseId":"web-security","studentName":"Aigerim","id":1}
```

`GET /enrollments` then returns:

```json
[{"courseId":"web-security","studentName":"Aigerim","id":1}]
```

A one-character `studentName` receives 422 with `loc: ["body", "studentName"]` and `msg: "String should have at least 2 characters"`. An unknown course receives 404 with `{"detail":"Course not found"}` for GET, like and enrollment. IDs use `len(ENROLLMENTS) + 1`; this lab intentionally has no database.

## Verify CORS

```bash
curl -i -H 'Origin: http://localhost:3000' http://localhost:8000/
curl -i -H 'Origin: http://evil.example' http://localhost:8000/
curl -i -X OPTIONS http://localhost:8000/enrollments -H 'Origin: http://localhost:3000' -H 'Access-Control-Request-Method: POST' -H 'Access-Control-Request-Headers: content-type'
```

Expected: allowed origin gets `access-control-allow-origin: http://localhost:3000` and `vary: Origin`; the foreign origin gets HTTP 200 without the allow-origin header; OPTIONS gets HTTP 200, POST in allowed methods, content-type in allowed headers and `access-control-max-age: 600`.

`GET /courses?is_elective=true` returns exactly `ai-integration` and `api-design`; `?isElective=true` is an unknown query parameter and returns all six courses. `?sort=title`, `?q=fastapi`, and `?page=2&page_size=2` keep their Lab 4 behavior.

## Bonus 3 Configurable origins

```bash
CORS_ORIGINS='http://localhost:3000,http://127.0.0.1:3000' fastapi dev main.py
```

The origin list is read with `os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")`. Both configured origins are permitted and a foreign origin remains unpermitted. Use exact origins separated by commas, without whitespace, paths or trailing slashes. If the variable is unset, only `http://localhost:3000` is permitted. In Next.js development mode the alternate frontend host also needs a temporary `allowedDevOrigins: ["127.0.0.1"]` setting.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Nine integration tests cover the complete HTTP contract, CORS/preflight, aliases, original queries, mutations, validation failures, unknown courses, and configurable origins. Start a fresh API process before the manual walkthrough to restore initial likes and enrollment numbering.

The frontend README contains the five-entry breakage journal. Its browser test uses temporary variants of this backend to reproduce missing CORS, a trailing slash, GET-only preflight methods, another frontend host, and an unhandled `KeyError: 'ofset'`. The shipped backend remains in the working configuration.
