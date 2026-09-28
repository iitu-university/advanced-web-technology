import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Course Catalog",
  description: "A course catalog built with Next.js App Router.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
          <nav className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <Link
              href="/"
              className="text-base font-bold tracking-tight text-slate-950"
            >
              Course Catalog
            </Link>
            <div className="flex items-center gap-2 text-sm font-medium">
              <Link
                href="/"
                className="rounded-md px-3 py-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
              >
                Home
              </Link>
              <Link
                href="/courses"
                className="rounded-md px-3 py-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
              >
                Courses
              </Link>
              <Link
                href="/about"
                className="rounded-md px-3 py-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
              >
                About
              </Link>
            </div>
          </nav>
        </header>
        <main className="min-h-[calc(100vh-65px)]">{children}</main>
      </body>
    </html>
  );
}
