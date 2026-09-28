import { notFound } from "next/navigation";
import { LikeButton } from "@/components/LikeButton";
import { getCourse, getCourses } from "@/lib/courses";

type CoursePageProps = {
  params: Promise<{ id: string }>;
};

export async function generateStaticParams() {
  const courses = await getCourses();

  return courses.map((course) => ({
    id: course.id,
  }));
}

export default async function CoursePage({ params }: CoursePageProps) {
  const { id } = await params;
  const course = await getCourse(id);

  if (!course) {
    notFound();
  }

  return (
    <section className="mx-auto w-full max-w-3xl px-6 py-12">
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-500">
        {course.isElective ? "Elective course" : "Core course"}
      </p>
      <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950">
        {course.title}
      </h1>
      <p className="mt-5 text-lg leading-8 text-slate-600">
        {course.description}
      </p>

      <div className="mt-8 flex flex-wrap items-center gap-4">
        <span className="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700">
          {course.credits} credits
        </span>
        <LikeButton initialLikes={course.likes} />
      </div>
    </section>
  );
}
