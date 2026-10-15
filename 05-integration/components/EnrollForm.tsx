"use client";

import { useState, type FormEvent } from "react";
import type { Enrollment } from "@/lib/courses";

const API = process.env.NEXT_PUBLIC_API_URL;

type Status = "idle" | "sending" | "done" | "rejected" | "error";
type ValidationError = { detail: { loc: (string | number)[]; msg: string; type: string }[] };

export function EnrollForm({ courseId }: { courseId: string }) {
  const [studentName, setStudentName] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (status === "sending") return;
    setStatus("sending");
    setMessage("");
    try {
      if (!API) throw new Error("NEXT_PUBLIC_API_URL is not set");
      const res = await fetch(`${API}/enrollments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ courseId, studentName }),
      });
      if (res.status === 422) {
        const rejected: ValidationError = await res.json();
        setMessage(rejected.detail[0].msg);
        setStatus("rejected");
        return;
      }
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const enrollment: Enrollment = await res.json();
      setMessage(`Enrollment number: ${enrollment.id}`);
      setStatus("done");
    } catch {
      setStatus("error");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex max-w-sm flex-col gap-2">
      <label htmlFor="studentName">Your name</label>
      <input
        id="studentName"
        value={studentName}
        onChange={(event) => setStudentName(event.target.value)}
        className="rounded-md border border-slate-300 px-3 py-2"
      />
      <button
        type="submit"
        disabled={status === "sending"}
        className="rounded-md border border-slate-300 px-3 py-2"
      >
        Enroll
      </button>
      {status === "done" && <p role="status">You are enrolled. {message}</p>}
      {status === "rejected" && (
        <p role="alert" className="text-red-600">The server rejected the data: {message}</p>
      )}
      {status === "error" && (
        <p role="alert" className="text-red-600">Could not submit the enrollment</p>
      )}
    </form>
  );
}
