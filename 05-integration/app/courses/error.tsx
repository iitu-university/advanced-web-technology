"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function CoursesError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="text-3xl font-bold">Something went wrong</h1>
      <p className="mb-6 mt-4 text-[var(--muted-foreground)]">
        Could not load the data. The backend may not be running.
      </p>
      <Button variant="outline" onClick={() => retry()}>Try again</Button>
    </main>
  );
}
