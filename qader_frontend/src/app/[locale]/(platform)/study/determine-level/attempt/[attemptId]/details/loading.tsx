"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const DetailsPageSkeleton = () => (
  <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
    <Card>
      <CardHeader>
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded-md" />
          <div className="space-y-2">
            <Skeleton className="h-7 w-48" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <Skeleton className="h-6 w-32" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        </div>
        <Skeleton className="h-px w-full" />
        <div className="space-y-4">
          <Skeleton className="h-6 w-40" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {[...Array(2)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        </div>
        <Skeleton className="h-px w-full" />
        <div className="space-y-4">
          <Skeleton className="h-6 w-48" />
          <div className="rounded-md border">
            <div className="space-y-px p-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
);

export default DetailsPageSkeleton;
