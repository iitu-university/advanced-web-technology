# Course Catalog

Course Catalog is a small Next.js App Router project for the Advanced Web Technologies course.

## Implemented

- Static routes for `/` and `/about`
- Server-rendered course list at `/courses`
- Dynamic route `/courses/[id]` with awaited `params`, `generateStaticParams`, and `notFound()`
- Shared navigation in `app/layout.tsx`
- Server component course cards with `next/link`
- Client component like button with local state
- Loading and not-found UI for course pages

## Getting Started

```bash
npm run dev
```

Open the printed local URL, usually `http://localhost:3000`.

## Useful Commands

```bash
npm run lint
npm run build
```
