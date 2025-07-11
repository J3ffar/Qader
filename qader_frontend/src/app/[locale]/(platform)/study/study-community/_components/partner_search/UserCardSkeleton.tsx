import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function UserCardSkeleton() {
  return (
    <Card className="p-4 flex items-center justify-between">
      <div className="flex items-center space-x-4 rtl:space-x-reverse">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-24" />
        </div>
      </div>
      <Skeleton className="h-10 w-28 rounded-md" />
    </Card>
  );
}
