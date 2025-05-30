// src/app/[locale]/(platform)/study/determine-level/start/loading.tsx
"use client";
import { Skeleton } from "@/components/ui/skeleton";

const StartLevelAssessmentPageSkeleton = () => {
  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Skeleton className="mx-auto mb-2 h-10 w-3/5" />
      <Skeleton className="mx-auto mb-8 h-5 w-4/5" />

      <div className="space-y-8">
        <div className="rounded-lg border">
          {" "}
          {/* Card Skeleton */}
          <div className="p-6">
            {" "}
            {/* CardHeader Skeleton */}
            <Skeleton className="mb-2 h-7 w-3/5" />
            <Skeleton className="h-4 w-4/5" />
          </div>
          <div className="space-y-6 p-6">
            {" "}
            {/* CardContent Skeleton */}
            <Skeleton className="mb-4 h-4 w-1/3" />{" "}
            {/* Error message placeholder */}
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div
                  key={i}
                  className="rounded-lg border p-4 dark:border-gray-700"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3 rtl:space-x-reverse">
                      <Skeleton className="h-6 w-6 rounded" />
                      <Skeleton className="h-5 w-32" />
                    </div>
                    <Skeleton className="h-6 w-6" /> {/* Chevron */}
                  </div>
                </div>
              ))}
            </div>
            <div>
              <Skeleton className="mb-2 h-6 w-1/4" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="mt-1 h-4 w-1/2" />
            </div>
          </div>
        </div>
        <div className="flex justify-end">
          <Skeleton className="h-12 w-32" />
        </div>
      </div>
    </div>
  );
};

export default StartLevelAssessmentPageSkeleton;
