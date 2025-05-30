"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AccordionItem, AccordionTrigger } from "@/components/ui/accordion"; // Only if needed

// This is the same skeleton component, defined here for Next.js loading.tsx convention
const DetermineLevelPageSkeleton = () => {
  const t = useTranslations("Study.determineLevel"); // Assuming translations are available in loading state
  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      <Card>
        <CardHeader className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <Skeleton className="mb-2 h-8 w-48" />
            <Skeleton className="h-4 w-72" />
          </div>
          <Skeleton className="h-10 w-48" />
        </CardHeader>
        <CardContent>
          <div className="mb-6 flex flex-col justify-between gap-4 rounded-lg border bg-card p-4 md:flex-row md:items-center">
            <Skeleton className="h-7 w-40" />
            <Skeleton className="h-10 w-[180px]" />
          </div>
          <div className="hidden md:block">
            <Table>
              <TableHeader>
                <TableRow>
                  {[...Array(7)].map(
                    (
                      _,
                      i // Increased to 7 for status column
                    ) => (
                      <TableHead key={i}>
                        <Skeleton className="h-5 w-20" />
                      </TableHead>
                    )
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {[...Array(3)].map((_, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <Skeleton className="h-5 w-20" />
                    </TableCell>
                    <TableCell className="text-center">
                      <Skeleton className="inline-block h-5 w-10" />
                    </TableCell>
                    <TableCell className="text-center">
                      <Skeleton className="inline-block h-5 w-10" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-6 w-16" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-6 w-16" />
                    </TableCell>
                    <TableCell className="text-center">
                      <Skeleton className="h-6 w-20" />
                    </TableCell>{" "}
                    {/* Status skeleton */}
                    <TableCell className="text-center">
                      <div className="flex justify-center gap-2">
                        <Skeleton className="h-9 w-24" />
                        <Skeleton className="h-9 w-24" />
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <div className="space-y-3 md:hidden">
            {[...Array(3)].map((_, i) => (
              <div
                key={`skeleton-mobile-${i}`}
                className="rounded-lg border p-4 dark:border-gray-700"
              >
                <div className="mb-2 flex w-full items-center justify-between">
                  <div className="text-start rtl:text-right">
                    <Skeleton className="mb-1 h-5 w-24" />
                    <Skeleton className="h-4 w-32" />
                  </div>
                  <Skeleton className="h-6 w-20" /> {/* Status placeholder */}
                </div>
                <Skeleton className="mb-1 h-4 w-1/2" />
                <Skeleton className="mb-1 h-4 w-1/2" />
                <Skeleton className="mb-3 h-4 w-1/2" />
                <div className="flex flex-col gap-2">
                  <Skeleton className="h-9 w-full" />
                  <Skeleton className="h-9 w-full" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DetermineLevelPageSkeleton;
