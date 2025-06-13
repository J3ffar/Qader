import { Skeleton } from "@/components/ui/skeleton";

// This component will be automatically rendered by Next.js while the page.tsx component is fetching data.
export default function Loading() {
  return (
    <div className="container mx-auto max-w-7xl animate-pulse p-4 md:p-6">
      <div className="mb-6 flex items-center justify-between">
        <Skeleton className="h-8 w-48 rounded-md" />
        <Skeleton className="h-9 w-28 rounded-md" />
      </div>

      <Skeleton className="mx-auto mb-6 h-2 max-w-3xl rounded-full" />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Main Question Area Skeleton */}
        <div className="space-y-6 lg:col-span-2">
          <Skeleton className="h-64 w-full rounded-xl" />
          <div className="flex items-center justify-between">
            <Skeleton className="h-10 w-32 rounded-md" />
            <Skeleton className="h-10 w-32 rounded-md" />
          </div>
        </div>

        {/* Sidebar Skeleton */}
        <div className="space-y-6 lg:col-span-1">
          <Skeleton className="h-32 w-full rounded-xl" />
          <Skeleton className="h-48 w-full rounded-xl" />
        </div>
      </div>
    </div>
  );
}
