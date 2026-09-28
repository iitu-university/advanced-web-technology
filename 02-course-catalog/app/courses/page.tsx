import { CourseCard } from "@/components/CourseCard";
import { getCourses } from "@/lib/courses";

export default async function CoursesPage() {
  const courses = await getCourses();

  return (
    <section className="mx-auto w-full max-w-5xl px-6 py-12">
      <div className="max-w-2xl">
        <h1 className="text-3xl font-bold tracking-tight text-slate-950">
          Courses
        </h1>
        <p className="mt-3 text-lg leading-8 text-slate-600">
          Choose a course to see details and try the local like counter.
        </p>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {courses.map((course) => (
          <CourseCard
            key={course.id}
            id={course.id}
            title={course.title}
            description={course.description}
            credits={course.credits}
            likes={course.likes}
          />
        ))}
      </div>
    </section>
  );
}
