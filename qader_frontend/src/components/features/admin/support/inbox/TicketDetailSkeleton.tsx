import { Skeleton } from "@/components/ui/skeleton";

export function TicketDetailSkeleton() {
  return (
    <div className="flex flex-col h-full p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 border-b pb-2">
        <Skeleton className="h-10 w-10 rounded-full" />
        <div className="grid gap-0.5">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-48" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Skeleton className="h-8 w-[150px]" />
          <Skeleton className="h-8 w-[150px]" />
        </div>
      </div>

      {/* Original Message */}
      <div className="p-4 rounded-lg bg-muted">
        <Skeleton className="h-5 w-3/4 mb-2" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
      </div>

      {/* Replies */}
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="flex items-end gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-20 w-full max-w-md rounded-lg" />
          </div>
        ))}
      </div>

      {/* Reply Form */}
      <div className="p-4 border-t bg-background mt-auto">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-10 w-10 mt-2 ml-auto" />
      </div>
    </div>
  );
}
