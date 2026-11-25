import "server-only";
import { cookies } from "next/headers";
import { SESSION_COOKIE } from "@/lib/session-cookie";

export async function saveToken(token: string, maxAgeSeconds: number) {
  (await cookies()).set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
    maxAge: maxAgeSeconds,
  });
}

export async function readToken() {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}

export async function deleteSession() {
  (await cookies()).delete(SESSION_COOKIE);
}
