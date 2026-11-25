"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/button";
import { login } from "./actions";

const fieldClass = "rounded-md border bg-[var(--background)] px-3 py-2";

export default function LoginPage() {
  const [state, action, pending] = useActionState(login, undefined);

  return (
    <main className="mx-auto max-w-sm px-4 py-14 sm:px-6">
      <h1 className="text-3xl font-bold tracking-tight">Log in</h1>
      <form action={action} className="mt-6 grid gap-4">
        <label className="grid gap-1.5 text-sm font-medium">
          E-mail
          <input name="email" type="email" autoComplete="username" required
            defaultValue={state?.email} className={fieldClass} />
        </label>
        <label className="grid gap-1.5 text-sm font-medium">
          Password
          <input name="password" type="password" autoComplete="current-password" required
            className={fieldClass} />
        </label>
        {state?.error && <p role="alert" className="text-sm text-red-600 dark:text-red-400">{state.error}</p>}
        <Button type="submit" variant="accent" disabled={pending}>
          {pending ? "Logging in…" : "Log in"}
        </Button>
      </form>
    </main>
  );
}
