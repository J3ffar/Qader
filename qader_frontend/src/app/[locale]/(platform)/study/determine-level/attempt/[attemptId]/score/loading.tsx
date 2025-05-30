"use client";

import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";

// Re-using the skeleton for loading.tsx
const ScorePageSkeleton = () => {
  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card className="max-w-3xl mx-auto">
        <CardHeader className="text-center">
          <Skeleton className="h-8 w-3/5 mx-auto mb-4" /> {/* Title */}
          <Skeleton className="h-10 w-28 mx-auto rounded-full" />{" "}
          {/* Score badge */}
        </CardHeader>
        <CardContent className="space-y-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-center">
            <Card className="p-4">
              <Skeleton className="h-7 w-7 mx-auto mb-2 rounded-full" />
              <Skeleton className="h-4 w-20 mx-auto mb-1" />
              <Skeleton className="h-6 w-16 mx-auto" />
            </Card>
            <Card className="p-4">
              <Skeleton className="h-7 w-7 mx-auto mb-2 rounded-full" />
              <Skeleton className="h-4 w-24 mx-auto mb-1" />
              <Skeleton className="h-6 w-12 mx-auto" />
            </Card>
          </div>
          <div>
            <Skeleton className="h-6 w-1/3 mx-auto mb-4" /> {/* Chart title */}
            <Skeleton className="h-64 w-full rounded-md" />{" "}
            {/* Chart placeholder */}
          </div>
          <Skeleton className="h-10 w-full rounded-md" />{" "}
          {/* Advice placeholder */}
        </CardContent>
        <CardFooter className="flex flex-col sm:flex-row justify-center gap-4 pt-8">
          <Skeleton className="h-12 w-36" />
          <Skeleton className="h-12 w-36" />
        </CardFooter>
      </Card>
    </div>
  );
};

export default ScorePageSkeleton;
