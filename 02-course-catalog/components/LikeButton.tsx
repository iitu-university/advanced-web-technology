"use client";

import { useState } from "react";

type LikeButtonProps = {
  initialLikes: number;
};

export function LikeButton({ initialLikes }: LikeButtonProps) {
  const [likes, setLikes] = useState<number>(initialLikes);

  return (
    <button
      type="button"
      onClick={() => setLikes((currentLikes) => currentLikes + 1)}
      className="rounded-md bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2"
      aria-label={`Like this course. Current likes: ${likes}`}
    >
      ❤ {likes}
    </button>
  );
}
