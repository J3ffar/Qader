"use client";

import { useState, useMemo } from "react";
import { useTranslations, useFormatter } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { useDebouncedCallback } from "use-debounce";
import { Filter, AlertCircle } from "lucide-react";

import { getAdminUsers } from "@/services/api/admin/users.service";
import { queryKeys } from "@/constants/queryKeys";
import { AdminUserListItem } from "@/types/api/admin/users.types";

import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { EmployeeTableSkeleton } from "./components/EmployeeTableSkeleton";
import EmployeeTableActions from "./components/EmployeeTableActions";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

const UserStatusBadge = ({ isActive }: { isActive: boolean }) => {
  const t = useTranslations("Admin.EmployeeManagement.statuses");
  const text = isActive ? t("active") : t("inactive");
  return (
    <Badge
      variant="outline"
      className={cn("text-xs", {
        "border-green-300 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-300":
          isActive,
        "border-gray-300 bg-gray-50 text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300":
          !isActive,
      })}
    >
      <span className="flex items-center gap-1.5">
        <span
          className={cn("h-2 w-2 rounded-full", {
            "bg-green-500": isActive,
            "bg-gray-500": !isActive,
          })}
        />
        {text}
      </span>
    </Badge>
  );
};

const ITEMS_PER_PAGE = 10;

export default function EmployeeClient() {
  const t = useTranslations("Admin.EmployeeManagement");
  const tRoles = useTranslations("Admin.EmployeeManagement.roles");
  const format = useFormatter();

  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<boolean | undefined>(
    undefined
  ); // undefined for all, true or false

  const employeeRoles = ["admin", "sub_admin", "teacher", "trainer"];

  const debouncedSearch = useDebouncedCallback((value: string) => {
    setSearchTerm(value);
    setCurrentPage(1); // Reset to first page on new search
  }, 300);

  const { data, isLoading, isError, error, isPlaceholderData, isFetching } =
    useQuery({
      queryKey: queryKeys.admin.users.list({
        roles: employeeRoles,
        page: currentPage,
        search: searchTerm,
        is_active: statusFilter,
      }),
      queryFn: () =>
        getAdminUsers({
          role: employeeRoles,
          page: currentPage,
          search: searchTerm,
          user__is_active: statusFilter,
          // page_size: ITEMS_PER_PAGE // If your API supports it
        }),
      placeholderData: (previousData) => previousData,
      staleTime: 5 * 1000, // 5 seconds
    });

  const users = useMemo(() => data?.results ?? [], [data]);
  const pageCount = data?.count ? Math.ceil(data.count / ITEMS_PER_PAGE) : 0;

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          {error.message || t("notifications.fetchError")}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("employeeList")}</CardTitle>
        <CardDescription>{t("employeeListDescription")}</CardDescription>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          <Input
            placeholder={t("searchPlaceholder")}
            className="max-w-sm"
            onChange={(e) => debouncedSearch(e.target.value)}
          />
          <div className="flex items-center gap-2">
            <Select
              value={
                statusFilter === undefined ? "all" : statusFilter.toString()
              }
              onValueChange={(value) => {
                setStatusFilter(value === "all" ? undefined : value === "true");
                setCurrentPage(1);
              }}
            >
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder={t("filter")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("allStatuses")}</SelectItem>
                <SelectItem value="true">{t("statuses.active")}</SelectItem>
                <SelectItem value="false">{t("statuses.inactive")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("table.id")}</TableHead>
                <TableHead>{t("table.name")}</TableHead>
                <TableHead className="hidden md:table-cell">
                  {t("table.email")}
                </TableHead>
                <TableHead>{t("table.role")}</TableHead>
                <TableHead>{t("table.status")}</TableHead>
                <TableHead className="hidden lg:table-cell">
                  {t("table.joinDate")}
                </TableHead>
                <TableHead>
                  <span className="sr-only">{t("table.actions")}</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <EmployeeTableSkeleton rows={ITEMS_PER_PAGE} />
              ) : users.length > 0 ? (
                users.map((emp) => (
                  <TableRow
                    key={emp.user_id}
                    className={isPlaceholderData ? "opacity-50" : ""}
                  >
                    <TableCell className="font-medium">{emp.user_id}</TableCell>
                    <TableCell className="font-semibold">
                      {emp.full_name}
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      {emp.user.email}
                    </TableCell>
                    <TableCell>{tRoles(emp.role)}</TableCell>
                    <TableCell>
                      <UserStatusBadge isActive={emp.user.is_active} />
                    </TableCell>
                    <TableCell className="hidden lg:table-cell">
                      {format.dateTime(new Date(emp.user.date_joined), {
                        dateStyle: "long",
                      })}
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
