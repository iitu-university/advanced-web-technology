import Link from "next/link";

type CourseCardProps = {
  id: string;
  title: string;
  description: string;
  credits: number;
  likes: number;
};

export function CourseCard({
  id,
  title,
  description,
  credits,
  likes,
}: CourseCardProps) {
  return (
    <Link
      href={`/courses/${id}`}
      className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
    >
      <h2 className="text-xl font-semibold text-slate-950 transition group-hover:text-slate-700">
        {title}
      </h2>
      <p className="mt-3 text-sm leading-6 text-slate-600">{description}</p>
      <div className="mt-5 flex items-center justify-between text-sm font-medium text-slate-500">
        <span>{credits} credits</span>
        <span aria-label={`${likes} likes`}>❤ {likes}</span>
      </div>
    </Link>
  );
}
