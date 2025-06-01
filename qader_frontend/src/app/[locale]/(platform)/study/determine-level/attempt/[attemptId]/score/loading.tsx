"use client";

// Assuming ScorePageSkeletonV2 is defined in page.tsx or imported from a shared components file
// For this structure, it's better to define Skeleton in its own file or ensure it's accessible.
// If ScorePageSkeletonV2 is in the page.tsx, we can copy its definition here or make it a shared component.
// For simplicity here, I'll copy the skeleton definition from the above page.tsx to this loading.tsx

import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";

const ScorePageSkeletonV2 = () => {
  // Copied definition
  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card className="mx-auto max-w-4xl">
        <CardHeader className="text-center">
          <Skeleton className="mx-auto mb-4 h-8 w-3/5" /> {/* Title */}
          <Skeleton className="mx-auto h-16 w-36 rounded-full" />{" "}
          {/* Score badge */}
        </CardHeader>
        <CardContent className="space-y-8 pt-6">
          {/* Skeletons for Gamification Stats */}
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Card key={`gamify-skel-${i}`} className="p-4">
                <Skeleton className="mx-auto mb-2 h-8 w-8 rounded-full" />
                <Skeleton className="mx-auto mb-1 h-4 w-3/4" />
                <Skeleton className="mx-auto h-6 w-1/2" />
              </Card>
            ))}
          </div>
          <Skeleton className="h-px w-full" /> {/* Separator Skeleton */}
          {/* Skeletons for Core Test Stats */}
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Card key={`core-skel-${i}`} className="p-4">
                <Skeleton className="mx-auto mb-2 h-8 w-8 rounded-full" />
                <Skeleton className="mx-auto mb-1 h-4 w-3/4" />
                <Skeleton className="mx-auto h-6 w-1/2" />
              </Card>
            ))}
          </div>
          {/* Skeletons for Score Distribution & Detailed Performance */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <Skeleton className="mx-auto mb-4 h-6 w-1/3" />{" "}
              {/* Chart/Detail title */}
              <Skeleton className="h-64 w-full rounded-md" />{" "}
              {/* Chart/Detail placeholder */}
            </div>
            <div>
              <Skeleton className="mx-auto mb-4 h-6 w-1/3" />{" "}
              {/* Chart/Detail title */}
              <Skeleton className="h-64 w-full rounded-md" />{" "}
              {/* Chart/Detail placeholder */}
            </div>
          </div>
          {/* Skeleton for Smart Analysis */}
          <Skeleton className="h-20 w-full rounded-md" />
        </CardContent>
        <CardFooter className="flex flex-col-reverse justify-center gap-3 pt-8 sm:flex-row sm:gap-4">
          <Skeleton className="h-12 w-full sm:w-40" />
          <Skeleton className="h-12 w-full sm:w-36" />
          <Skeleton className="h-12 w-full sm:w-40" />
        </CardFooter>
      </Card>
    </div>
  );
};

export default ScorePageSkeletonV2;
