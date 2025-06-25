"use client";

import { useTranslations } from "next-intl";
import {
  ArrowUpDown,
  Filter,
  MoreHorizontal,
  Plus,
  Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// Mock data to represent the employee list
const mockEmployees = [
  {
    id: 1,
    name: "سعيد أحمد",
    email: "sa123ah@gmail.com",
    status: "active",
    joinDate: "23/2/25",
  },
  {
    id: 2,
    name: "سعيد أحمد",
    email: "sa123ah@gmail.com",
    status: "active",
    joinDate: "23/2/25",
    isHighlighted: true,
  },
  {
    id: 3,
    name: "سعيد أحمد",
    email: "sa123ah@gmail.com",
    status: "blocked",
    joinDate: "23/2/25",
  },
  {
    id: 4,
    name: "سعيد أحمد",
    email: "sa123ah@gmail.com",
    status: "active",
    joinDate: "23/2/25",
  },
  {
    id: 5,
    name: "سعيد أحمد",
    email: "sa123ah@gmail.com",
    status: "active",
    joinDate: "23/2/25",
  },
  {
    id: 6,
    name: "سعيد أحمد",
    email: "sa123ah@gmail.com",
    status: "blocked",
    joinDate: "23/2/25",
  },
];

type Status = "active" | "blocked";

const StatusBadge = ({ status }: { status: Status }) => {
  const t = useTranslations("Admin.AdminDashboard.statuses");
  const statusMap: Record<
    Status,
    { variant: "default" | "destructive" | "secondary"; text: string }
  > = {
    active: { variant: "default", text: t("active") },
    blocked: { variant: "destructive", text: t("blocked") },
  };

  const currentStatus = statusMap[status];

  return (
    <Badge
      variant={currentStatus.variant}
      className={cn("text-xs font-normal", {
        "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300":
          status === "active",
        "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300":
          status === "blocked",
      })}
    >
      <span className="flex items-center gap-1.5">
        <span
          className={cn("h-2 w-2 rounded-full", {
            "bg-green-500": status === "active",
            "bg-red-500": status === "blocked",
          })}
        ></span>
        {currentStatus.text}
      </span>
    </Badge>
  );
};

export default function AdminDashboardPage() {
  const t = useTranslations("Admin.AdminDashboard");

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-muted-foreground">{t("description")}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline">
            <Upload className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
            {t("export")}
          </Button>
          <Button>
            <Plus className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
            {t("addEmployee")}
          </Button>
        </div>
      </div>

      {/* Main Content Card */}
      <Card>
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
            <Button variant="outline" className="gap-1">
              <ArrowUpDown className="h-3.5 w-3.5" />
              <span className="sr-only sm:not-sr-only sm:whitespace-nowrap">
                {t("sort")}
              </span>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("table.id")}</TableHead>
                <TableHead>{t("table.name")}</TableHead>
                <TableHead>{t("table.email")}</TableHead>
                <TableHead>{t("table.status")}</TableHead>
                <TableHead>{t("table.joinDate")}</TableHead>
                <TableHead>
                  <span className="sr-only">{t("table.actions")}</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockEmployees.map((emp) => (
                <TableRow
                  key={emp.id}
                  className={cn({ "bg-muted/80": emp.isHighlighted })}
                >
                  <TableCell className="font-medium">{emp.id}</TableCell>
                  <TableCell className="font-semibold">{emp.name}</TableCell>
                  <TableCell>{emp.email}</TableCell>
                  <TableCell>
                    <StatusBadge status={emp.status as Status} />
                  </TableCell>
                  <TableCell>{emp.joinDate}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          aria-haspopup="true"
                          size="icon"
                          variant="ghost"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                          <span className="sr-only">{t("toggleMenu")}</span>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>{t("actions")}</DropdownMenuLabel>
                        <DropdownMenuItem>{t("viewDetails")}</DropdownMenuItem>
                        <DropdownMenuItem>{t("editUser")}</DropdownMenuItem>
                        <DropdownMenuItem className="text-destructive">
                          {t("deleteUser")}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
