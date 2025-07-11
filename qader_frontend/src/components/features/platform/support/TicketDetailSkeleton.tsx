// src/components/features/platform/support/TicketDetailSkeleton.tsx
import { Skeleton } from "@/components/ui/skeleton";

export function TicketDetailSkeleton() {
  return (
    <div className="flex flex-col h-[calc(100vh-120px)] p-4" dir="rtl">
      {/* Header Skeleton */}
      <div className="border-b pb-4 mb-4">
        <Skeleton className="h-8 w-3/4 mb-2" />
        <Skeleton className="h-4 w-1/3" />
      </div>

      {/* Chat Bubbles Skeleton */}
      <div className="flex-1 space-y-6">
        <div className="flex items-end gap-3 justify-start">
          <Skeleton className="h-8 w-8 rounded-full" />
          <Skeleton className="h-16 w-1/2 rounded-lg" />
        </div>
        <div className="flex items-end gap-3 justify-end">
          <Skeleton className="h-20 w-3/5 rounded-lg" />
          <Skeleton className="h-8 w-8 rounded-full" />
        </div>
        <div className="flex items-end gap-3 justify-start">
          <Skeleton className="h-8 w-8 rounded-full" />
          <Skeleton className="h-12 w-2/5 rounded-lg" />
        </div>
      </div>

      {/* Reply Form Skeleton */}
      <div className="mt-auto pt-4 border-t">
        <div className="flex items-center gap-4">
          <Skeleton className="h-12 flex-1 rounded-lg" />
          <Skeleton className="h-10 w-10 rounded-lg" />
        </div>
      </div>
    </div>
  );
}
