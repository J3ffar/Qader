"use client";

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

interface TestHistoryTabProps {
  userId: number;
}

export function TestHistoryTab({ userId }: TestHistoryTabProps) {
  const t = useTranslations("Admin.StudentManagement");
  const tCommon = useTranslations("Common");
  const format = useFormatter();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.admin.users.testHistory(userId),
    queryFn: () => getAdminUserTestHistory(userId),
  });

  const attempts = data?.results ?? [];

  if (isLoading) {
    return (
      <div className="space-y-2 py-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <Alert variant="destructive" className="mt-4">
        <AlertTitle>{tCommon("error")}</AlertTitle>
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="border rounded-md">
      <Table>
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
      </Table>
    </div>
  );
}
