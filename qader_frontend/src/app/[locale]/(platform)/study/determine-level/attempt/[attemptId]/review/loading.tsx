"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { FilterIcon, FileText, TrendingUp } from "lucide-react";

const ReviewPageSkeleton = () => {
  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      {/* Header Card Skeleton */}
      <Card className="overflow-hidden">
        <CardHeader className="bg-muted/20 p-4 sm:p-5">
          <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
            <div className="flex items-center gap-2">
              <Skeleton className="h-10 w-10 rounded-md" /> {/* Back button */}
              <div className="flex items-center gap-2.5">
                <FileText className="h-[1.3em] w-[1.3em] text-muted-foreground/50" />
                <Skeleton className="h-7 w-40 sm:w-56" /> {/* Title */}
              </div>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 rounded-lg border bg-background p-2 px-3">
              <TrendingUp className="me-1 h-4 w-4 text-muted-foreground/50 rtl:me-0 rtl:ms-1" />
              <Skeleton className="h-4 w-10" />
              <Skeleton className="h-4 w-px bg-muted-foreground/20" />
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-4 w-px bg-muted-foreground/20" />
              <Skeleton className="h-4 w-12" />
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Filter Controls Card Skeleton */}
      <Card>
        <CardContent className="p-3 sm:p-4">
          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center text-sm">
              <FilterIcon className="me-2 h-4 w-4 text-muted-foreground/50 rtl:me-0 rtl:ms-2" />
              <Skeleton className="h-5 w-16" /> {/* "Filter By:" */}
            </div>
            <div className="grid w-full grid-cols-3 gap-1 sm:flex sm:w-auto">
              <Skeleton className="h-9 flex-1 rounded-md" />
              <Skeleton className="h-9 flex-1 rounded-md" />
              <Skeleton className="h-9 flex-1 rounded-md" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Question Card Skeleton */}
      <Card className="w-full shadow-lg">
        <CardHeader>
          <div className="mb-3 flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between">
            <Skeleton className="h-5 w-28" /> {/* Question X of Y */}
            <Skeleton className="h-7 w-24 rounded-md" /> {/* Status Badge */}
          </div>
          <Skeleton className="mb-2 h-6 w-full" /> {/* Question Text Line 1 */}
          <Skeleton className="h-6 w-4/5" /> {/* Question Text Line 2 */}
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-px w-full bg-border" /> {/* Separator */}
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="flex items-start space-x-3 rounded-md border p-3.5 rtl:space-x-reverse"
              >
                <Skeleton className="mt-0.5 h-5 w-5 flex-shrink-0 rounded-full" />
                <Skeleton className="mt-0.5 h-5 w-6" />
                <Skeleton className="h-5 flex-1" />
              </div>
            ))}
          </div>
          <Skeleton className="mt-4 h-12 w-full rounded-md" />{" "}
          {/* Accordion 1 */}
          <Skeleton className="mt-2 h-12 w-full rounded-md" />{" "}
          {/* Accordion 2 */}
        </CardContent>
      </Card>

      {/* Navigation Controls Skeleton */}
      <div className="mt-6 flex items-center justify-between rounded-lg border bg-card p-2.5 shadow-sm sm:p-3">
        <Skeleton className="h-11 w-32 rounded-md sm:w-36" />
        <Skeleton className="h-5 w-20 sm:w-24" />
        <Skeleton className="h-11 w-32 rounded-md sm:w-36" />
      </div>
    </div>
  );
};

export default ReviewPageSkeleton;
