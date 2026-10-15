"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { Course } from "@/lib/courses";

const API = process.env.NEXT_PUBLIC_API_URL;

type LikeButtonProps = {
  courseId: string;
  initialLikes: number;
  courseTitle: string;
};

export function LikeButton({ courseId, initialLikes, courseTitle }: LikeButtonProps) {
  const [likes, setLikes] = useState(initialLikes);
  const [failed, setFailed] = useState(false);
  const [sending, setSending] = useState(false);

  async function handleClick() {
    if (sending) return;
    setFailed(false);
    setSending(true);
    try {
      if (!API) throw new Error("NEXT_PUBLIC_API_URL is not set");
      const res = await fetch(`${API}/courses/${encodeURIComponent(courseId)}/like`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const course: Course = await res.json();
      setLikes(course.likes);
    } catch {
      setFailed(true);
    } finally {
      setSending(false);
    }
  }

  return (
    <div>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        aria-label={`Like ${courseTitle}`}
        aria-busy={sending}
        disabled={sending}
        onClick={handleClick}
      >
        ♥ {likes}
      </Button>
      {failed && <p role="alert" className="mt-2 text-sm text-red-600">Failed to like the course</p>}
    </div>
  );
}
