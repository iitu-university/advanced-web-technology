import "server-only";
import { cache } from "react";
import { redirect } from "next/navigation";
import { API_URL } from "@/lib/api";
import { readToken } from "@/lib/session";

type CurrentUser = {
  id: number;
  email: string;
  role: "student" | "admin";
  studentId: number | null;
};

export const getSession = cache(async () => {
  const token = await readToken();
  if (!token) return null;

  const response = await fetch(`${API_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (response.status === 401) return null;
  if (!response.ok) throw new Error(`API error: ${response.status}`);

  const user: CurrentUser = await response.json();
  return { user, token };
});

export async function verifySession() {
  const session = await getSession();
  if (!session) redirect("/login");
  return session;
}
