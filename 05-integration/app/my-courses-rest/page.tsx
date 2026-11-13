import { getJson } from "@/lib/api";

type Student = { id: number; name: string; email: string };
type Enrollment = { id: number; courseId: string };
type Course = { id: string; title: string; credits: number; level: string };

export default async function MyCoursesRestPage() {
  const [student, enrollments] = await Promise.all([
    getJson<Student>("/students/2"),
    getJson<Enrollment[]>("/students/2/enrollments"),
  ]);
  const courses = await Promise.all(
    enrollments.map((enrollment) =>
      getJson<Course>(`/courses/${enrollment.courseId}`),
    ),
  );

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="text-2xl font-bold">My courses: {student.name}</h1>
      <ul className="mt-4 list-disc pl-6">
        {courses.map((course) => (
          <li key={course.id}>
            {course.title} — {course.credits} credits, level: {course.level}
          </li>
        ))}
      </ul>
    </main>
  );
}
