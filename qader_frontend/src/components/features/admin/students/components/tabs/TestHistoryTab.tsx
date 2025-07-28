"use client";

import { useState } from "react"; // 1. Import useState
import { useQuery } from "@tanstack/react-query";
import { useFormatter, useTranslations } from "next-intl";
import { getAdminUserTestHistory } from "@/services/api/admin/users.service";
import { queryKeys } from "@/constants/queryKeys";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { DataTablePagination } from "@/components/shared/DataTablePagination"; // Reusing our pagination component

interface TestHistoryTabProps {
  userId: number;
}

const ITEMS_PER_PAGE = 20; // Define how many items to show per page

export function TestHistoryTab({ userId }: TestHistoryTabProps) {
  const t = useTranslations("Admin.StudentManagement");
  const tCommon = useTranslations("Common");
  const format = useFormatter();

  // 1. State for pagination
  const [currentPage, setCurrentPage] = useState(1);

  // 2. Make the query page-aware
  const { data, isLoading, isError, error, isFetching } = useQuery({
    queryKey: queryKeys.admin.users.testHistory(userId, currentPage),
    queryFn: () => getAdminUserTestHistory(userId, { page: currentPage }),
    placeholderData: (previousData) => previousData, // keepPreviousData equivalent in v5
    staleTime: 5 * 1000,
  });

  const attempts = data?.results ?? [];
  const pageCount = data?.count ? Math.ceil(data.count / ITEMS_PER_PAGE) : 0;

  const renderContent = () => {
    if (isLoading) {
      return (
        <TableBody>
          {Array.from({ length: 5 }).map((_, i) => (
            <TableRow key={i}>
              <TableCell colSpan={4}>
                <Skeleton className="h-8 w-full" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      );
    }

    if (isError) {
      return (
        <TableBody>
          <TableRow>
            <TableCell colSpan={4}>
              <Alert variant="destructive" className="mt-4">
                <AlertTitle>{tCommon("error")}</AlertTitle>
                <AlertDescription>{error.message}</AlertDescription>
              </Alert>
            </TableCell>
          </TableRow>
        </TableBody>
      );
    }

    return (
      <TableBody>
        {attempts.length > 0 ? (
          attempts.map((attempt) => (
            <TableRow key={attempt.attempt_id}>
              <TableCell className="font-semibold">
                {attempt.test_type}
              </TableCell>
              <TableCell>
                {format.dateTime(new Date(attempt.date), {
                  dateStyle: "medium",
                })}
              </TableCell>
              <TableCell>
                <Badge
                  variant={
                    attempt.status === "completed" ? "default" : "secondary"
                  }
                >
                  {attempt.status_display}
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                {attempt.score_percentage !== null
                  ? `${Math.round(attempt.score_percentage)}%`
                  : "N/A"}
              </TableCell>
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell colSpan={4} className="h-24 text-center">
              {t("noTestHistory")}
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    );
  };

  return (
    <div className="space-y-4">
      <div className="border rounded-md">
        <Table dir="rtl">
          <TableHeader>
            <TableRow>
              <TableHead>{t("tabs.testHistoryTable.type")}</TableHead>
              <TableHead>{t("tabs.testHistoryTable.date")}</TableHead>
              <TableHead>{t("tabs.testHistoryTable.status")}</TableHead>
              <TableHead className="text-right">
                {t("tabs.testHistoryTable.score")}
              </TableHead>
            </TableRow>
          </TableHeader>
          {renderContent()}
        </Table>
      </div>
      {/* 3. Add pagination controls */}
      {pageCount > 1 && (
        <DataTablePagination
          page={currentPage}
          pageCount={pageCount}
          setPage={setCurrentPage}
          canPreviousPage={currentPage > 1}
          canNextPage={currentPage < pageCount}
          isFetching={isFetching}
        />
      )}
    </div>
  );
}
