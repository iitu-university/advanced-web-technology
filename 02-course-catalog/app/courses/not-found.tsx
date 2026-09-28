import Link from "next/link";

export default function CourseNotFound() {
  return (
    <section className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-bold tracking-tight text-slate-950">
        Course not found
      </h1>
      <p className="mt-4 text-lg leading-8 text-slate-600">
        The course you requested does not exist in this catalog.
      </p>
      <Link
        href="/courses"
        className="mt-6 inline-flex rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
      >
        Back to courses
      </Link>
    </section>
  );
}
