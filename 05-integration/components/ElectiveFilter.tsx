"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import type { Course } from "@/lib/courses";

const API = process.env.NEXT_PUBLIC_API_URL;

async function fetcher(url: string): Promise<Course[]> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export function ElectiveFilter() {
  const [onlyElective, setOnlyElective] = useState(false);
  const query = onlyElective ? "?is_elective=true" : "";
  const { data, error, isLoading } = useSWR<Course[]>(
    API ? `${API}/courses${query}` : null,
    fetcher,
  );

  return (
    <div>
      <label className="mb-6 flex items-center gap-3">
        <input
          type="checkbox"
          checked={onlyElective}
          onChange={(event) => setOnlyElective(event.target.checked)}
          className="h-4 w-4 accent-[var(--color-brand)]"
        />
        Electives only
      </label>
      {!API && <p role="alert">NEXT_PUBLIC_API_URL is not set: create .env.local</p>}
      {error && <p role="alert" className="text-red-600">Failed to load courses</p>}
      {isLoading && <p role="status">Loading...</p>}
      {data && (
        <ul className="divide-y rounded-xl border bg-[var(--card)] px-5">
          {data.map((course) => (
            <li key={course.id} className="py-4">
              <Link href={`/courses/${course.id}`} className="font-medium hover:text-brand">
                {course.title}
              </Link>
              <span className="text-[var(--muted-foreground)]">
                {` — ${course.credits} cr.`}{course.isElective && " · elective"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
