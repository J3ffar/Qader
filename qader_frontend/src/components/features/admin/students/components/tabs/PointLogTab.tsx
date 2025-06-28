"use client";

import { useState } from "react"; // 1. Import useState
import { useQuery } from "@tanstack/react-query";
import { useTranslations, useFormatter } from "next-intl";
import { getAdminUserPointLog } from "@/services/api/admin/users.service";
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
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface PointLogTabProps {
  userId: number;
}

const ITEMS_PER_PAGE = 20; // Point log can be denser

export function PointLogTab({ userId }: PointLogTabProps) {
  const t = useTranslations("Admin.StudentManagement");
  const tCommon = useTranslations("Common");
  const format = useFormatter();

  // 1. State for pagination
  const [currentPage, setCurrentPage] = useState(1);

  // 2. Make the query page-aware
  const { data, isLoading, isError, error, isFetching } = useQuery({
    queryKey: queryKeys.admin.users.pointLog(userId, currentPage),
    queryFn: () => getAdminUserPointLog(userId, { page: currentPage }),
    placeholderData: (previousData) => previousData,
    staleTime: 5 * 1000,
  });

  const logs = data?.results ?? [];
  const pageCount = data?.count ? Math.ceil(data.count / ITEMS_PER_PAGE) : 0;
  console.log(logs);
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
        {logs.length > 0 ? (
          logs.map((log) => (
            <TableRow key={log.id}>
              <TableCell className="font-semibold">
                <Badge
                  variant={log.points_change > 0 ? "secondary" : "outline"}
                  className={cn(
                    "font-mono",
                    log.points_change > 0 && "text-green-600",
                    log.points_change < 0 && "text-red-600"
                  )}
                >
                  {log.points_change > 0
                    ? `+${log.points_change}`
                    : log.points_change}
                </Badge>
              </TableCell>
              <TableCell>{log.reason_code_display}</TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {log.description}
              </TableCell>
              <TableCell className=" text-xs text-muted-foreground">
                {format.dateTime(new Date(log.timestamp), {
                  dateStyle: "short",
                  timeStyle: "short",
                })}
              </TableCell>
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell colSpan={4} className="h-24 text-center">
              {t("noPointHistory")}
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
              <TableHead className="w-[100px]">{t("table.points")}</TableHead>
              <TableHead>{t("form.reasonLabel")}</TableHead>
              <TableHead>{t("descriptionPoint")}</TableHead>
              <TableHead className="text-right">{t("table.date")}</TableHead>
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
