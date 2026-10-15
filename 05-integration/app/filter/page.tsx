import { ElectiveFilter } from "@/components/ElectiveFilter";

export default function FilterPage() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <h1 className="mb-6 text-3xl font-bold">Course filter</h1>
      <ElectiveFilter />
    </main>
  );
}
