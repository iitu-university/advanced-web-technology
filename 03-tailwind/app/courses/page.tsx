import { CourseCard } from "@/components/CourseCard";
import { getCourses } from "@/lib/courses";

export default async function CoursesPage() {
  const courses = await getCourses();
  return (
    <main className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <div className="mb-10 max-w-2xl">
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-brand">Course catalog</p>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Choose a course that moves you forward.</h1>
        <p className="mt-3 text-[var(--muted-foreground)]">Six courses for every stage of your web development journey.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {courses.map((course) => <CourseCard key={course.id} {...course} />)}
      </div>
    </main>
  );
}
