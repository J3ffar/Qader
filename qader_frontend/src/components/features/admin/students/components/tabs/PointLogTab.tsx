"use client";

import { useQuery } from "@tanstack/react-query";
import { useFormatter, useTranslations } from "next-intl";
import { queryKeys } from "@/constants/queryKeys";
import { getAdminUserPointLog } from "@/services/api/admin/users.service";
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
import { cn } from "@/lib/utils";

interface PointLogTabProps {
  userId: number;
}

export function PointLogTab({ userId }: PointLogTabProps) {
  const t = useTranslations("Admin.StudentManagement");
  const tCommon = useTranslations("Common");
  const format = useFormatter();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.admin.users.pointLog(userId),
    queryFn: () => getAdminUserPointLog(userId),
  });

  const logs = data?.results ?? [];

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
            <TableHead className="w-[100px]">{t("table.points")}</TableHead>
            <TableHead>{t("form.reasonLabel")}</TableHead>
            <TableHead>{t("descriptionPoint")}</TableHead>
            <TableHead className="text-right">{t("table.date")}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {logs.length > 0 ? (
            logs.map((log) => (
              <TableRow key={log.id}>
                <TableCell>
                  <Badge
                    variant={log.points > 0 ? "default" : "destructive"}
                    className={cn(
                      "font-mono",
                      log.points > 0 && "text-green-600",
                      log.points < 0 && "text-red-600"
                    )}
                  >
                    {log.points > 0 ? `+${log.points}` : log.points}
                  </Badge>
                </TableCell>
                <TableCell>{log.reason}</TableCell>
                <TableCell>{log.description}</TableCell>
                <TableCell className="text-right text-xs text-muted-foreground">
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
      </Table>
    </div>
  );
}
