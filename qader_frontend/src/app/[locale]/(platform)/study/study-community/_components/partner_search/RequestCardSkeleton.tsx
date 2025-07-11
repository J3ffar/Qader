import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function RequestCardSkeleton() {
  return (
    <Card className="p-3 flex items-center justify-between">
      <div className="flex items-center space-x-4 rtl:space-x-reverse">
        <Skeleton className="h-10 w-10 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-3 w-20" />
        </div>
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-9 w-20 rounded-md" />
        <Skeleton className="h-9 w-20 rounded-md" />
      </div>
    </Card>
  );
}
