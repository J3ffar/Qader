"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardFooter } from "@/components/ui/card";

export function ChallengeCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-[150px]" />
            <Skeleton className="h-3 w-[100px]" />
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <Skeleton className="h-5 w-[80px]" />
          <Skeleton className="h-4 w-[60px]" />
        </div>
      </CardContent>
      <CardFooter className="p-4 pt-0 flex justify-end">
        <Skeleton className="h-8 w-[100px]" />
      </CardFooter>
    </Card>
  );
}

export function ChallengesListSkeleton() {
  return (
    <div className="grid gap-4">
      <ChallengeCardSkeleton />
      <ChallengeCardSkeleton />
      <ChallengeCardSkeleton />
    </div>
  );
}
