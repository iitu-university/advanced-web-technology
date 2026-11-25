"use server";

import { redirect } from "next/navigation";
import { API_URL } from "@/lib/api";
import { verifySession } from "@/lib/dal";

type EnrollmentState = { error: string } | { id: number } | undefined;

export async function enroll(
  courseId: string,
  _previous: EnrollmentState,
  formData: FormData,
): Promise<EnrollmentState> {
  const { user, token } = await verifySession();
  const studentId = user.role === "admin" ? Number(formData.get("studentId")) : user.studentId;
  if (studentId === null) return { error: "Your account has no student profile." };
  if (!Number.isSafeInteger(studentId) || studentId < 1) return { error: "Enter a valid student ID." };

  let response: Response;
  try {
    response = await fetch(`${API_URL}/enrollments`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ courseId, studentId }),
      cache: "no-store",
    });
  } catch {
    return { error: "Could not submit the enrollment." };
  }
  if (response.status === 401) redirect("/login");
  if (response.status === 409) return { error: "This student is already enrolled." };
  if (response.status === 404) return { error: "Course or student not found." };
  if (!response.ok) return { error: "Could not submit the enrollment." };

  const { id } = await response.json();
  return { id };
}
