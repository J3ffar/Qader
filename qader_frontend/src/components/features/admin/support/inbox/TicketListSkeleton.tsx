import { Skeleton } from "@/components/ui/skeleton";

export function TicketListSkeleton() {
  return (
    <div className="p-4 space-y-3">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className="flex flex-col items-start gap-2 rounded-lg border p-3"
        >
          <div className="flex w-full items-center justify-between">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-12" />
          </div>
          <Skeleton className="h-4 w-full" />
          <div className="flex w-full items-center justify-between">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-16" />
          </div>
        </div>
      ))}
    </div>
  );
}
