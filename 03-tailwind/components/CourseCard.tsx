import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LikeButton } from "@/components/LikeButton";
import type { Course } from "@/lib/courses";

export function CourseCard({ id, title, description, credits, likes, isElective }: Course) {
  return (
    <Link href={`/courses/${id}`} className="block h-full rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand">
      <Card className="flex h-full flex-col transition-all hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-md dark:hover:border-blue-700 dark:hover:shadow-black/30">
        <CardHeader>
          <div className="mb-2 flex items-center justify-between gap-2">
            <Badge variant="secondary">{isElective ? "Elective" : "Required"}</Badge>
            <span className="text-xs font-medium text-[var(--muted-foreground)]">{credits} credits</span>
          </div>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col gap-5">
          <p className="flex-1 text-sm leading-6 text-[var(--muted-foreground)]">{description}</p>
          <div className="flex items-center justify-between border-t pt-4">
            <span className="text-xs font-medium text-[var(--muted-foreground)]">Explore course</span>
            <LikeButton initialLikes={likes} courseTitle={title} />
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
