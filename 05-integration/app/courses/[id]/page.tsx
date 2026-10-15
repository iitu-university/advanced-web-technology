import Link from "next/link";
import { notFound } from "next/navigation";
import { buttonVariants } from "@/components/ui/button";
import { getCourse } from "@/lib/courses";
import { LikeButton } from "@/components/LikeButton";
import { EnrollForm } from "@/components/EnrollForm";

// No generateStaticParams: course data is loaded at request time.
export default async function CoursePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const course = await getCourse(id);
  if (!course) notFound();

  return (
    <main className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <p className="text-sm font-semibold text-brand">
        {course.isElective ? "Elective" : "Required"} · {course.credits} credits
      </p>
      <h1 className="mt-3 text-4xl font-bold tracking-tight">{course.title}</h1>
      <p className="mt-6 text-lg leading-8 text-[var(--muted-foreground)]">{course.description}</p>
      <div className="mt-6">
        <LikeButton courseId={course.id} initialLikes={course.likes} courseTitle={course.title} />
      </div>
      <section className="mt-8 border-t pt-8">
        <h2 className="mb-4 text-xl font-semibold">Enroll in this course</h2>
        <EnrollForm courseId={course.id} />
      </section>
      <Link href="/courses" className={`${buttonVariants({ variant: "accent" })} mt-8`}>
        Back to catalog
      </Link>
    </main>
  );
}
