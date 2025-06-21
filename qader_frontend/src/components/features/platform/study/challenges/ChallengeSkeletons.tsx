"use client";

import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";

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

const PlayerCardSkeleton = () => (
  <div className="flex flex-col items-center gap-4">
    <Skeleton className="h-24 w-24 rounded-full" />
    <Skeleton className="h-6 w-32" />
    <Skeleton className="h-10 w-24" />
  </div>
);

export function ChallengesListSkeleton() {
  return (
    <div className="grid gap-4">
      <ChallengeCardSkeleton />
      <ChallengeCardSkeleton />
      <ChallengeCardSkeleton />
    </div>
  );
}

export const ChallengeSkeletons = {
  RoomSkeleton: () => (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <Skeleton className="h-8 w-1/2 mx-auto" />
        <Skeleton className="h-5 w-1/3 mx-auto mt-2" />
      </CardHeader>
      <CardContent className="p-6 md:p-8">
        <div className="flex flex-col md:flex-row items-center justify-around gap-8">
          <PlayerCardSkeleton />
          <div className="text-4xl font-bold text-muted-foreground">
            <Skeleton className="h-10 w-16" />
          </div>
          <PlayerCardSkeleton />
        </div>
        <div className="mt-8 flex justify-center">
          <Skeleton className="h-12 w-48" />
        </div>
      </CardContent>
    </Card>
  ),
};
