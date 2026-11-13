# Advanced Web Technologies

The numbered directories preserve the progression of the course project. Labs 6–8 use the six-course catalog introduced by the FastAPI backend in Labs 4–5.

| Directory | Work |
|---|---|
| `01-github-explorer` | HTML/CSS/JavaScript GitHub repository search, filtering and local storage |
| `02-course-catalog` | Next.js App Router, typed local data, server/client components and dynamic course routes |
| `03-tailwind` | Responsive catalog with Tailwind and reusable UI components |
| `04-backend` | FastAPI backend from Lab 4, integrated in Lab 5, continued with SQLAlchemy/Alembic in Lab 7, and GraphQL in **Lab 8** |
| `05-integration` | Lab 5 Next.js/FastAPI integration and Lab 8 REST/GraphQL comparison pages |
| `06-database` | **Lab 6** PostgreSQL schema, seed, route queries, experiments and report |

Start with [Lab 6 instructions and report](06-database/README.md), then [Lab 7 and Lab 8 instructions and reports](04-backend/README.md). Lab 8 continues the existing API and adds the paired frontend pages in `05-integration`.

Labs 7 and 8 intentionally stay in `04-backend`, because their assignments continue the existing API. It changes enrollment requests from `studentName` to `studentId`; the frontend is left at the Lab 5 version as required by the assignment. Read its compatibility notes before testing the old enrollment form.

The Lab 7 work remains in the backend directory, and Lab 8 extends it in place. The handouts describe standalone GitHub submissions named `course-catalog-db`, `course-catalog-api`, and `course-catalog`; this workspace keeps the projects together in one repository.

