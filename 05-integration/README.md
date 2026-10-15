# Lab 5 Frontend and Backend Integration

Next.js renders the course catalog from FastAPI. The browser calls FastAPI directly for the SWR filter, likes, and enrollment. The backend uses camelCase JSON and keeps mutations in memory. This project continues the catalog from Labs 1–3 with the Lab 3 styles.

## Run both applications

Use Node.js 20+ and Python 3.10+. Start the backend first, then the frontend in a second terminal. Open the frontend at **http://localhost:3000**, exactly: `127.0.0.1` and a different port are different origins.

In this course workspace:

```bash
cd 04-backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
fastapi dev main.py
```

```bash
cd 05-integration
npm ci
cp .env.example .env.local
npm run dev -- --port 3000
```

In the two standalone repositories, replace `04-backend` with `course-catalog-api` and `05-integration` with `course-catalog`. The source files themselves have the same paths relative to each project root.

Backend Swagger: http://localhost:8000/docs. Frontend routes: `/`, `/about`, `/courses`, `/courses/web-security`, and `/filter`.

## Environment variables

Create `.env.local` next to `package.json`:

```dotenv
API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

`API_URL` is read by the Next.js server in `lib/courses.ts`. `NEXT_PUBLIC_API_URL` is included in the browser bundle and is read only by Client Components. Client Components import types from `lib/courses.ts` with `import type`, so the server module is not executed in the browser. Never put secrets in a `NEXT_PUBLIC_` variable. Restart the dev server after initially creating the file; rebuild before production use if the public URL changes.

`.env.local` is ignored by Git. `.env.example` contains the reproducible example values.

## Request paths and contract

| Action | Request sender | FastAPI request | CORS and preflight |
| --- | --- | --- | --- |
| `/courses` | Next.js Server Component | `GET /courses` | Browser CORS does not apply |
| `/courses/[id]` | Next.js Server Component | `GET /courses/{course_id}` | Browser CORS does not apply |
| Electives only | Browser with SWR | `GET /courses?is_elective=true` | CORS; no preflight |
| Like | Browser | `POST /courses/{course_id}/like` | CORS; no preflight |
| Enrollment | Browser | `POST /enrollments`, JSON | CORS; `OPTIONS` before POST |

JSON fields are `isElective`, `courseId`, and `studentName`; the query parameter stays `is_elective`. The initial catalog has six courses ordered by popularity, with `ai-integration` first and `api-design` last. The elective filter returns exactly those two courses. Likes and enrollments survive a page reload, but reset when FastAPI restarts.

The enrollment form deliberately has no client name-length constraint: submitting `A` reaches the server and displays its 422 message, `String should have at least 2 characters`. Submitting `Aigerim` returns 201 and displays the assigned enrollment number. No failed validation creates a record.

## Decisions

`generateStaticParams` from Lab 1 is absent because course data now belongs to the backend; fetching the list while building would fail when the backend is stopped and could freeze data. Both server fetches use `cache: "no-store"`, check `res.ok`, and map course 404 to `undefined` and `notFound()`; other failures reach `error.tsx`, whose `retry()` requests fresh server data. A like POST has no body or special headers and is a simple request, while JSON enrollment sets `Content-Type: application/json` and needs a preflight; permission is cached for 600 seconds unless the browser cache is disabled.

The final Next.js config enables neither Cache Components nor partial prefetching. Next.js 16.4.0 supplies the `retry` error-boundary prop. Like buttons are outside course links, so clicking a like does not navigate to the detail page.

## Verification

Run backend checks from its root:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Run frontend checks from its root while the backend is stopped:

```bash
npm run lint
npm run typecheck
npm run build
```

The verified build passes with no backend process and reports:

```text
○ /
○ /_not-found
○ /about
ƒ /courses
ƒ /courses/[id]
○ /filter
```

For real browser verification, stop any project processes on ports 3000 and 8000 first. The test starts and stops its own production Next.js and temporary FastAPI servers; all broken variants are generated in a temporary directory, leaving the application source unchanged.

```bash
npx playwright install chromium
npm run test:browser
```

For standalone sibling repositories:

```bash
BACKEND_DIR=../course-catalog-api npm run test:browser
```

If using installed Chrome on macOS:

```bash
BROWSER_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm run test:browser
```

`BACKEND_PYTHON` can override the backend Python executable. The backend dependencies must already be installed in its `.venv`.

Verified on 13 October 2026 (Asia/Almaty), with Next.js 16.4.0 and Chromium 153.0.8010.52:

- Nine backend integration tests pass, including all six documented operations, camelCase aliases, Lab 4 search/sort/pagination, persistent likes, 201/404/422 responses, CORS, and the bonus.
- ESLint and TypeScript pass. The build succeeds with the backend stopped.
- Browser checks cover six server-rendered cards without browser API requests; two likes followed by a reload; server validation for `A`; enrollment for `Aigerim`; the server enrollment list; six/two/six SWR results; and course not-found.
- CDP Network records show no OPTIONS for likes, OPTIONS 200 before the first enrollment POST 422, a cached permission before POST 201, and OPTIONS again when cache is disabled.
- A temporary one-second backend delay displays `loading.tsx`. With the backend stopped both course routes display `error.tsx`; starting it and clicking “Try again” restores the page without a manual reload.
- All five required faults below were reproduced with real browser requests. The final source contains none of those faults.

Evidence: [browser results and headers](verification/browser-results.json), [backend logs and traceback](verification/backend-experiments.log), [build output](verification/build.log), and [backend test output](verification/backend-tests.log). Screenshots: [catalog](verification/courses.png), [enrollment](verification/course-enrolled.png), [422 rejection](verification/validation-422.png), and [elective filter](verification/filter-electives.png).

## Breakage journal

Each experiment changes one condition, uses a fresh browser context with cache disabled, and checks the filter, like, enrollment, and server-rendered catalog. The logs and console quotes are actual results in `verification/`. Browser Network can show a provisional failed POST row after a rejected preflight; that does not mean POST reached FastAPI. The backend logs prove which requests were executed.

### Breakage 1 Remove CORS entirely

- What I did: replaced the complete `app.add_middleware(CORSMiddleware, ...)` block with no middleware in a temporary copy of `main.py`.
- Console: “Access to fetch at 'http://localhost:8000/courses' from origin 'http://localhost:3000' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.”
- Network: GET courses and POST like fail with `MissingAllowOriginHeader`; backend logs show 200 for both. The like still changes 21 to 22 on the server. OPTIONS enrollments returns **405**; enrollment POST is not sent. `/courses` still renders six cards.
- Cause: responses contain no `access-control-allow-origin` because CORS middleware is absent. CORS hides responses from browser JavaScript and does not stop the simple request from executing.
- How I found it: steps 2–3 show the missing header, step 4 distinguishes the 405 preflight from an origin refusal, and the backend logs in step 5 confirm execution.

### Breakage 2 Trailing slash in the origin

- What I did: changed the resolved `allow_origins=["http://localhost:3000"]` to `allow_origins=["http://localhost:3000/"]` in the temporary backend.
- Console: “No 'Access-Control-Allow-Origin' header is present on the requested resource”; enrollment also says “Response to preflight request doesn't pass access control check”.
- Network: GET courses and POST like are blocked although the backend returns 200; the server like count increases. OPTIONS enrollments returns **400**, no enrollment POST reaches the backend. `/courses` works. The manual preflight body is `Disallowed CORS origin`.
- Cause: an origin has scheme, host and port with no trailing slash. The configured string does not exactly match `Origin: http://localhost:3000`.
- How I found it: step 3 compares the exact origin strings; step 4 and the manual OPTIONS body identify the origin refusal.

### Breakage 3 Remove allowed methods

- What I did: removed `allow_methods=["*"]`, leaving CORSMiddleware's default GET-only preflight allowance.
- Console: “Response to preflight request doesn't pass access control check: It does not have HTTP ok status.”
- Network: GET courses and POST like both return **200** and work; simple requests do not check the preflight method list. OPTIONS enrollments returns **400**, with `access-control-allow-origin: http://localhost:3000` and `access-control-allow-methods: GET`. The enrollment POST is not sent. `/courses` works. The manual preflight body is `Disallowed CORS method`.
- Cause: the preflight asks for POST but only GET is allowed. The origin header is correct; the method list is wrong.
- How I found it: step 4 checks the OPTIONS status, allowed methods header and response body.

### Breakage 4 Open another host

- What I did: left the backend origin as `http://localhost:3000` and opened the frontend at `http://127.0.0.1:3000`. The automated matrix uses `next start`, which does not require a development-host exception. For the separate dev-server reproduction, temporarily add `allowedDevOrigins: ["127.0.0.1"]` to `next.config.ts`, restart `npm run dev`, then remove it afterwards.
- Console: “Access to fetch at 'http://localhost:8000/courses' from origin 'http://127.0.0.1:3000' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.”
- Network: GET courses and POST like are blocked, backend logs show **200**, and the like still increments. OPTIONS enrollments returns **400**, no enrollment POST reaches the backend. `/courses` still works because Next.js sends its own API request.
- Cause: localhost and 127.0.0.1 are different hosts and therefore different origins even on the same computer.
- How I found it: step 3 compares the request origin with the allowed origin; step 4 confirms `Disallowed CORS origin` in the manual preflight. Opening localhost fixes it; the bonus also allows explicitly configuring both origins.

### Breakage 5 Python error masquerading as CORS

- What I did: changed `return courses[p["offset"] : p["offset"] + p["limit"]]` to `return courses[p["ofset"] : p["offset"] + p["limit"]]` in the temporary backend.
- Console: “No 'Access-Control-Allow-Origin' header is present on the requested resource” on `/filter`; production React also logs its error-boundary exception.
- Network: GET courses is blocked by CORS, but the backend logs **500** and `KeyError: 'ofset'`. Like POST returns **200**; enrollment OPTIONS returns **200** and POST **201**. `/courses` displays “Something went wrong”.
- Cause: the unhandled KeyError creates a 500 response outside CORSMiddleware, without CORS headers. The configuration itself is correct.
- How I found it: step 2 checks the status, then step 5 reads the backend traceback. The Server Component fails too, proving this is an API failure. Restoring `p["offset"]` fixes both catalog views.

## Manual CORS checks

```bash
curl -i -H 'Origin: http://localhost:3000' http://localhost:8000/
curl -i -H 'Origin: http://evil.example' http://localhost:8000/
curl -i -X OPTIONS http://localhost:8000/enrollments -H 'Origin: http://localhost:3000' -H 'Access-Control-Request-Method: POST' -H 'Access-Control-Request-Headers: content-type'
```

Expected: the allowed origin gets `access-control-allow-origin` and `vary: Origin`; the foreign origin gets HTTP 200 without permission; valid OPTIONS gets HTTP 200, allowed origin/method/header and `access-control-max-age: 600`.

## Bonus 3 Origins from an environment variable

Backend configuration:

```python
allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
```

Run the backend with:

```bash
CORS_ORIGINS='http://localhost:3000,http://127.0.0.1:3000' fastapi dev main.py
```

Both origins receive their exact `access-control-allow-origin` value; `http://evil.example` receives none. Comma-separated origins must contain no paths, trailing slashes or extra spaces. The normal default remains only `http://localhost:3000`. See [bonus curl output](verification/bonus-origins.log) and the dedicated backend test.

## Submission

Submit the frontend and backend repository links from the course instructions. The workspace keeps the frontend in `05-integration` and the backend in `04-backend`; the standalone repositories keep their project files at the root. Today's integration history has at least five meaningful frontend commits and three meaningful backend commits, plus verification and documentation.
