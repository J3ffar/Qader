"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  ArrowLeft,
  ArrowRight,
  Filter,
  ChevronLeft,
  ChevronRight,
  //   Scoreboard,
} from "lucide-react"; // Import icons used in actual page

const ReviewPageSkeleton = () => {
  // Determine icon direction based on a common approach or simplify for skeleton
  // For simplicity, we'll use a fixed direction or omit the specific logic here.
  const isLocaleAr = false; // Simplified for skeleton

  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      {/* Header Section Skeleton */}
      <div className="mb-6 flex flex-col items-center justify-between gap-4 sm:flex-row">
        <div className="flex items-center gap-2">
          <Skeleton className="h-10 w-10 rounded-md" /> {/* Back button icon */}
          <Skeleton className="h-8 w-48" /> {/* Title "Review Your Attempt" */}
        </div>
        <Card className="p-3 opacity-50 shadow-sm">
          {" "}
          {/* Score summary card */}
          <div className="flex items-center gap-3 text-sm">
            {/* <Scoreboard className="h-5 w-5 text-muted-foreground" /> */}
            <Skeleton className="h-5 w-20" />
            <Skeleton className="h-5 w-16" />
            <Skeleton className="h-5 w-16" />
          </div>
        </Card>
      </div>

      {/* Filter Controls Skeleton */}
      <div className="flex flex-col items-center justify-between gap-4 rounded-lg border bg-card p-4 shadow-sm sm:flex-row">
        <div className="flex items-center text-sm font-medium">
          <Filter className="me-2 h-5 w-5 text-muted-foreground rtl:me-0 rtl:ms-2" />
          <Skeleton className="h-5 w-20" /> {/* "Filter By:" */}
        </div>
        <div className="flex flex-wrap justify-center gap-2 sm:justify-end">
          <Skeleton className="h-9 w-28 rounded-md" /> {/* Filter option 1 */}
          <Skeleton className="h-9 w-32 rounded-md" /> {/* Filter option 2 */}
          <Skeleton className="h-9 w-32 rounded-md" /> {/* Filter option 3 */}
        </div>
      </div>

      {/* Main Question Card Skeleton */}
      <Card className="w-full shadow-lg">
        <CardHeader>
          <div className="mb-2 flex items-center justify-between">
            <Skeleton className="h-6 w-1/4" /> {/* Question X of Y */}
            <Skeleton className="h-6 w-20 rounded-full" />{" "}
            {/* Correct/Incorrect Badge */}
          </div>
          <Skeleton className="mb-1 h-5 w-full" /> {/* Question Text Line 1 */}
          <Skeleton className="h-5 w-3/4" /> {/* Question Text Line 2 */}
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="flex items-center space-x-3 rounded-md border border-border p-3 rtl:space-x-reverse"
              >
                <Skeleton className="h-5 w-5 rounded-full" />{" "}
                {/* Icon placeholder */}
                <Skeleton className="h-5 w-6" /> {/* Option Letter */}
                <Skeleton className="h-5 flex-1" /> {/* Option Text */}
              </div>
            ))}
          </div>
          {/* Accordion Skeletons */}
          <Skeleton className="mt-4 h-10 w-full rounded-md" />{" "}
          {/* Accordion Trigger 1 */}
          <Skeleton className="mt-2 h-10 w-full rounded-md" />{" "}
          {/* Accordion Trigger 2 */}
        </CardContent>
      </Card>

      {/* Navigation Controls Skeleton */}
      <div className="mt-6 flex items-center justify-between">
        <Skeleton className="h-12 w-36 rounded-md" /> {/* Previous Button */}
        <Skeleton className="h-5 w-24" /> {/* Question X of Y text */}
        <Skeleton className="h-12 w-36 rounded-md" /> {/* Next Button */}
      </div>
    </div>
  );
};

export default ReviewPageSkeleton;
