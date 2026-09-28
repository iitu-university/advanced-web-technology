import Link from "next/link";

export default function Home() {
  return (
    <section className="mx-auto flex w-full max-w-4xl flex-1 flex-col justify-center px-6 py-20">
      <p className="mb-3 text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
        Advanced Web Technologies
      </p>
      <h1 className="max-w-2xl text-4xl font-bold tracking-tight text-slate-950 sm:text-6xl">
        Course Catalog
      </h1>
      <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
        Welcome to a small catalog of semester courses built with the Next.js
        App Router, TypeScript, and server components.
      </p>
      <Link
        href="/courses"
        className="mt-8 inline-flex w-fit rounded-md bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
      >
        Browse courses
      </Link>
    </section>
  );
}
