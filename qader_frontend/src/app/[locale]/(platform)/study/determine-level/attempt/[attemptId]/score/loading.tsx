"use client";

import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";

const ScorePageSkeleton = () => {
  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card className="mx-auto max-w-4xl">
        <CardHeader className="text-center">
          <Skeleton className="mx-auto mb-4 h-8 w-3/5" /> {/* Title */}
          <Skeleton className="mx-auto h-12 w-32 rounded-full" />{" "}
          {/* Score badge */}
        </CardHeader>
        <CardContent className="space-y-8 pt-6">
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map(
              (
                _,
                i // Skeleton for 4 stat cards
              ) => (
                <Card key={i} className="p-4">
                  <Skeleton className="mx-auto mb-2 h-8 w-8 rounded-full" />
                  <Skeleton className="mx-auto mb-1 h-4 w-3/4" />
                  <Skeleton className="mx-auto h-6 w-1/2" />
                </Card>
              )
            )}
          </div>
          <div>
            <Skeleton className="mx-auto mb-4 h-6 w-1/3" /> {/* Chart title */}
            <Skeleton className="h-64 w-full rounded-md" />{" "}
            {/* Chart placeholder */}
          </div>
          <Skeleton className="h-12 w-full rounded-md" />{" "}
          {/* Advice placeholder */}
        </CardContent>
        <CardFooter className="flex flex-col-reverse justify-center gap-3 pt-8 sm:flex-row sm:gap-4">
          <Skeleton className="h-12 w-full sm:w-40" /> {/* Back to overview */}
          <Skeleton className="h-12 w-full sm:w-36" /> {/* Retake */}
          <Skeleton className="h-12 w-full sm:w-40" /> {/* Review */}
        </CardFooter>
      </Card>
    </div>
  );
};

export default ScorePageSkeleton;
