"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/button";
import { enroll } from "@/app/courses/[id]/actions";

export function EnrollForm({ courseId, isAdmin }: { courseId: string; isAdmin: boolean }) {
  const [state, action, pending] = useActionState(enroll.bind(null, courseId), undefined);

  return (
    <form action={action} className="grid max-w-sm justify-items-start gap-3">
      {isAdmin && (
        <label className="grid gap-1.5 text-sm font-medium">
          Student ID
          <input name="studentId" type="number" min="1" required
            className="rounded-md border bg-[var(--background)] px-3 py-2" />
        </label>
      )}
      <Button type="submit" variant="outline" disabled={pending}>
        {pending ? "Enrolling…" : "Enroll"}
      </Button>
      {state && "id" in state && <p role="status">Enrollment number: {state.id}</p>}
      {state && "error" in state && <p role="alert" className="text-red-600 dark:text-red-400">{state.error}</p>}
    </form>
  );
}
