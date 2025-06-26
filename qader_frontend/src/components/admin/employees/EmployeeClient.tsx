"use client";

import { useState, useMemo } from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { getAdminUsers } from "@/services/admin.service";
import { queryKeys } from "@/constants/queryKeys";
import { DataTablePagination } from "@/components/shared/DataTablePagination";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Filter } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { AdminUserListItem } from "@/types/api/admin.types";
import EmployeeTableActions from "./EmployeeTableActions";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

// UserStatusBadge component is unchanged...
const UserStatusBadge = ({ isActive }: { isActive: boolean }) => {
  const t = useTranslations("Admin.EmployeeManagement.statuses");
  const text = isActive ? t("active") : t("inactive");
  return (
    <Badge
      variant={isActive ? "default" : "secondary"}
      className={cn("text-xs font-normal", {
        "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300":
          isActive,
        "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300":
          !isActive,
      })}
    >
      <span className="flex items-center gap-1.5">
        <span
          className={cn("h-2 w-2 rounded-full", {
            "bg-green-500": isActive,
            "bg-gray-500": !isActive,
          })}
        ></span>
        {text}
      </span>
    </Badge>
  );
};

const ITEMS_PER_PAGE = 20;

export default function EmployeeClient() {
  const t = useTranslations("Admin.EmployeeManagement");
  const tRoles = useTranslations("Admin.EmployeeManagement.roles");

  const [currentPage, setCurrentPage] = useState(1);
  const employeeRoles = ["admin", "sub_admin", "teacher", "trainer"];

  // --- Start of Changes ---
  // 2. Destructure isFetching from useQuery for the pagination component
  const { data, isLoading, isError, error, isPlaceholderData, isFetching } =
    useQuery({
      queryKey: queryKeys.admin.users.list({
        roles: employeeRoles,
        page: currentPage,
      }),
      queryFn: () =>
        getAdminUsers({
          role: employeeRoles,
          page: currentPage,
        }),
      placeholderData: (previousData) => previousData,
    });

  const users = useMemo(() => data?.results ?? [], [data]);

  // 3. Calculate pageCount and other props needed by DataTablePagination
  const pageCount = data?.count ? Math.ceil(data.count / ITEMS_PER_PAGE) : 0;
  // --- End of Changes ---

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          {error.message || "Failed to fetch employees."}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      {/* CardHeader is unchanged */}
      <CardHeader>
        <CardTitle>{t("employeeList")}</CardTitle>
        <CardDescription>{t("employeeListDescription")}</CardDescription>
        <div className="mt-4 flex items-center gap-2">
          <Input placeholder={t("searchPlaceholder")} className="max-w-sm" />
          <Button variant="outline" className="gap-1">
            <Filter className="h-3.5 w-3.5" />
            <span className="sr-only sm:not-sr-only sm:whitespace-nowrap">
              {t("filter")}
            </span>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            {/* TableHeader is unchanged */}
            <TableHeader>
              <TableRow>
                <TableHead>{t("table.id")}</TableHead>
                <TableHead>{t("table.name")}</TableHead>
                <TableHead>{t("table.email")}</TableHead>
                <TableHead>{t("table.role")}</TableHead>
                <TableHead>{t("table.status")}</TableHead>
                <TableHead>{t("table.joinDate")}</TableHead>
                <TableHead>
                  <span className="sr-only">{t("table.actions")}</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading && users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center">
                    Loading employees...
                  </TableCell>
                </TableRow>
              ) : users.length > 0 ? (
                users.map((emp) => (
                  <TableRow
                    key={emp.user_id}
                    className={
                      isPlaceholderData ? "opacity-50 transition-opacity" : ""
                    }
                  >
                    <TableCell className="font-medium">{emp.user_id}</TableCell>
                    <TableCell className="font-semibold">
                      {emp.full_name}
                    </TableCell>
                    <TableCell>{emp.user.email}</TableCell>
                    <TableCell>{tRoles(emp.role)}</TableCell>
                    <TableCell>
                      <UserStatusBadge isActive={emp.user.is_active} />
                    </TableCell>
                    <TableCell>
                      {new Date(emp.user.date_joined).toLocaleDateString(
                        "en-CA"
                      )}
                    </TableCell>
                    <TableCell>
                      <EmployeeTableActions userId={emp.user_id} />
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center">
                    No employees found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        <DataTablePagination
          page={currentPage}
          pageCount={pageCount}
          setPage={setCurrentPage}
          canPreviousPage={currentPage > 1}
          canNextPage={currentPage < pageCount}
          isFetching={isFetching}
        />
      </CardContent>
    </Card>
  );
}
