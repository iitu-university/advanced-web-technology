import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
      <div className="max-w-2xl">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-brand">Learn by building</p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">Find your next web technology course.</h1>
        <p className="mt-6 text-lg leading-8 text-[var(--muted-foreground)]">A curated, responsive course catalog for learners who want practical skills and a clear path forward.</p>
        <Link href="/courses" className={`${buttonVariants({ variant: "accent", size: "lg" })} mt-8`}>Browse all courses</Link>
      </div>
    </main>
  );
}
