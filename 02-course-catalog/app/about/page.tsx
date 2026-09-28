export default function About() {
  return (
    <section className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-bold tracking-tight text-slate-950">
        About this catalog
      </h1>
      <div className="mt-6 space-y-4 text-lg leading-8 text-slate-600">
        <p>
          This project is a course catalog for the Advanced Web Technologies
          course. It demonstrates file-based routing, server components, dynamic
          routes, and typed data in a Next.js App Router application.
        </p>
        <p>
          The catalog uses local mock data for now, so the pages behave like a
          real app before a backend API is added in a later lab.
        </p>
      </div>
    </section>
  );
}
