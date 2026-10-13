import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";

export default function CourseNotFound() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="text-3xl font-bold">Course not found</h1>
      <p className="mt-4 text-[var(--muted-foreground)]">
        The course you requested does not exist in this catalog.
      </p>
      <Link href="/courses" className={`${buttonVariants({ variant: "accent" })} mt-6`}>
        Back to courses
      </Link>
    </main>
  );
}
