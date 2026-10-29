# Advanced Web Technologies

The numbered directories preserve the progression of the course project. Labs 6 and 7 use the six-course catalog introduced by the FastAPI backend in Labs 4–5.

| Directory | Work |
|---|---|
| `01-github-explorer` | HTML/CSS/JavaScript GitHub repository search, filtering and local storage |
| `02-course-catalog` | Next.js App Router, typed local data, server/client components and dynamic course routes |
| `03-tailwind` | Responsive catalog with Tailwind and reusable UI components |
| `04-backend` | FastAPI backend from Lab 4, integrated in Lab 5 and continued with SQLAlchemy/Alembic in **Lab 7** |
| `05-integration` | Lab 5 Next.js/FastAPI integration and its historical browser evidence |
| `06-database` | **Lab 6** PostgreSQL schema, seed, route queries, experiments and report |

Start with [Lab 6 instructions and report](06-database/README.md), then [Lab 7 instructions and report](04-backend/README.md). The detailed [project review and requirement mapping](PROJECT_REVIEW.md) explains how the new work continues the earlier labs and where each requirement is verified.

Lab 7 intentionally stays in `04-backend`, because its assignment continues the existing API. It changes enrollment requests from `studentName` to `studentId`; the frontend is left at the Lab 5 version as required by the assignment. Read its compatibility notes before testing the old enrollment form.

The implementation is on `codex/labs-6-7`, with separate meaningful commits for both labs. The handouts describe standalone GitHub submissions named `course-catalog-db` and `course-catalog-api`; publication is a separate step from the local implementation. No GitHub repository or remote branch was created by this work.
