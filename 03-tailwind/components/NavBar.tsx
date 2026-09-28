"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Home" },
  { href: "/courses", label: "Courses" },
  { href: "/about", label: "About" },
];

export function NavBar() {
  const pathname = usePathname();
  return (
    <nav aria-label="Main navigation" className="border-b border-slate-800 bg-slate-950 text-slate-100 shadow-sm">
      <div className="mx-auto flex max-w-6xl items-center gap-2 px-4 py-3 sm:px-6">
        <Link href="/" className="mr-2 text-sm font-bold tracking-tight text-white">Course Catalog</Link>
        {links.map((link) => {
          const active = pathname === link.href;
          return <Link key={link.href} href={link.href} className={cn("rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-blue-300", active && "bg-slate-800 text-blue-300")}>{link.label}</Link>;
        })}
      </div>
    </nav>
  );
}
