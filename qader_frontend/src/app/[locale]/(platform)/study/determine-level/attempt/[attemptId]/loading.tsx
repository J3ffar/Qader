// src/app/[locale]/(platform)/study/determine-level/attempt/[attemptId]/loading.tsx
"use client";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";

// Re-using the skeleton component for the loading.tsx file
const QuizPageSkeleton = () => {
  return (
    <div className="container mx-auto flex flex-col items-center p-4 md:p-6 lg:p-8">
      <Card className="w-full max-w-3xl">
        <CardHeader className="pb-4">
          <div className="mb-3 flex items-center justify-between">
            <Skeleton className="h-7 w-1/2" />
            <Skeleton className="h-8 w-24" />
          </div>
          <div className="flex items-center justify-between text-sm">
            <Skeleton className="h-5 w-1/3" />
            <Skeleton className="h-5 w-1/4" />
          </div>
          <Skeleton className="mt-2 h-2 w-full" />
        </CardHeader>
        <CardContent className="min-h-[250px] py-6">
          <Skeleton className="mb-6 h-6 w-3/4" />
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="flex items-center space-x-3 rtl:space-x-reverse"
              >
                <Skeleton className="h-5 w-5 rounded-full" />
                <Skeleton className="h-10 flex-1 rounded-md" />
              </div>
            ))}
          </div>
        </CardContent>
        <CardFooter className="flex flex-col items-center justify-between gap-3 pt-6 sm:flex-row">
          <Skeleton className="h-10 w-full sm:w-28" />
          <Skeleton className="h-10 w-full sm:w-28" />
        </CardFooter>
      </Card>
    </div>
  );
};

export default QuizPageSkeleton;
