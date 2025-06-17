import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function StatisticsDashboardSkeleton() {
  return (
    <div className="grid animate-pulse grid-cols-1 gap-6">
      {/* Row 1: Key Stats Cards Skeleton (now 5 cards) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-28 w-full" />
        ))}
      </div>

      {/* Row 2: Main Chart Skeleton (full width) */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <Skeleton className="h-7 w-48" />
            <Skeleton className="h-10 w-40" />
          </div>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>

      {/* Grid for subsequent rows */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Row 3 Skeletons */}
        <div className="lg:col-span-7">
          <Card>
            <CardHeader>
              <Skeleton className="h-7 w-1/3" />
              <Skeleton className="mt-2 h-5 w-2/3" />
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <Skeleton className="h-40 w-full rounded-lg" />
              <Skeleton className="h-40 w-full rounded-lg" />
            </CardContent>
          </Card>
        </div>
        <div className="lg:col-span-5">
          <Card>
            <CardHeader>
              <Skeleton className="h-7 w-3/4" />
              <Skeleton className="mt-2 h-5 w-full" />
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
              <div className="mt-4 space-y-4">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Row 4 Skeletons */}
        <div className="lg:col-span-7">
          <Card>
            <CardHeader>
              <Skeleton className="h-7 w-1/2" />
              <Skeleton className="mt-2 h-5 w-3/4" />
            </CardHeader>
            <CardContent className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </CardContent>
          </Card>
        </div>
        <div className="lg:col-span-5">
          <Card>
            <CardHeader>
              <Skeleton className="h-7 w-1/2" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-6 w-full" />
              <Skeleton className="h-6 w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
