"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

type LikeButtonProps = {
  initialLikes: number;
  courseTitle: string;
};

export function LikeButton({ initialLikes, courseTitle }: LikeButtonProps) {
  const [likes, setLikes] = useState(initialLikes);

  return (
    <Button
      variant="ghost"
      size="sm"
      aria-label={`Like ${courseTitle}`}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        setLikes((currentLikes) => currentLikes + 1);
      }}
    >
      ♥ {likes}
    </Button>
  );
}
