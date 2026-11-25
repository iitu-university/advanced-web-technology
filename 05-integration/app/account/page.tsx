import { Button } from "@/components/ui/button";
import { verifySession } from "@/lib/dal";
import { logout } from "./actions";

export default async function AccountPage() {
  const { user } = await verifySession();

  return (
    <main className="mx-auto max-w-2xl px-4 py-14 sm:px-6">
      <h1 className="text-3xl font-bold tracking-tight">Account</h1>
      <dl className="mt-6 grid grid-cols-[auto_1fr] gap-x-5 gap-y-2 rounded-lg border bg-[var(--card)] p-5 text-sm">
        <dt className="font-medium">E-mail</dt>
        <dd className="break-all">{user.email}</dd>
        <dt className="font-medium">Role</dt>
        <dd>{user.role}</dd>
      </dl>
      <form action={logout} className="mt-6">
        <Button type="submit" variant="outline">Log out</Button>
      </form>
    </main>
  );
}
