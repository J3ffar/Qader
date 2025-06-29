import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { MoreHorizontal, Trash2, Eye } from "lucide-react";
import { useMutation } from "@tanstack/react-query";

import type {
  SupportTicket,
  TicketPriority,
  TicketStatus,
} from "@/types/api/admin/support.types";
import { deleteSupportTicket } from "@/services/api/admin/support.service";
import { queryKeys } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { SupportTableToolbar } from "./SupportTableToolbar"; // To be created
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";

// --- Status & Priority Badges ---
const statusVariantMap: Record<
  TicketStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  open: "default",
  pending_admin: "secondary",
  pending_user: "outline",
  closed: "destructive",
};

const priorityVariantMap: Record<
  TicketPriority,
  "destructive" | "default" | "secondary"
> = {
  1: "destructive",
  2: "default",
  3: "secondary",
};

// --- Table Actions Column ---
function TicketActions({ ticket }: { ticket: SupportTicket }) {
  const t = useTranslations("Admin.support.actions");
  const queryClient = useQueryClient();
  const router = useRouter();

  const { mutate: performDelete, isLoading: isDeleting } = useMutation({
    mutationFn: () => deleteSupportTicket(ticket.id),
    onSuccess: () => {
      toast.success(t("deleteSuccess"));
      queryClient.invalidateQueries(queryKeys.admin.support.lists());
    },
    onError: () => {
      toast.error(t("deleteError"));
    },
  });

  return (
    <ConfirmationDialog
      title={t("deleteConfirmTitle")}
      description={t("deleteConfirmDescription")}
      onConfirm={performDelete}
      isConfirming={isDeleting}
    >
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-8 w-8 p-0">
            <span className="sr-only">Open menu</span>
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onClick={() =>
              router.push(`${PATHS.ADMIN.SUPPORT_MANAGEMENT}/${ticket.id}`)
            }
          >
            <Eye className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
            {t("viewDetails")}
          </DropdownMenuItem>
          <DropdownMenuItem
            className="text-destructive focus:text-destructive"
            asChild
          >
            <button className="w-full">
              <Trash2 className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
              {t("delete")}
            </button>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </ConfirmationDialog>
  );
}

// --- Main Table Component ---
interface SupportTableProps {
  data: SupportTicket[];
  pageCount: number;
  filters: Record<string, string>;
  onFilterChange: (key: string, value: string | null) => void;
}

export function SupportTable({
  data,
  pageCount,
  filters,
  onFilterChange,
}: SupportTableProps) {
  const t = useTranslations("Admin.support");
  const tStatus = useTranslations("Admin.support.statusLabels");
  const tPriority = useTranslations("Admin.support.priorityLabels");

  return (
    <div className="space-y-4">
      <SupportTableToolbar filters={filters} onFilterChange={onFilterChange} />
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("table.subject")}</TableHead>
              <TableHead>{t("table.user")}</TableHead>
              <TableHead>{t("table.status")}</TableHead>
              <TableHead>{t("table.priority")}</TableHead>
              <TableHead>{t("table.assignedTo")}</TableHead>
              <TableHead>{t("table.lastUpdate")}</TableHead>
              <TableHead>{t("table.actions")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.length > 0 ? (
              data.map((ticket) => (
                <TableRow key={ticket.id}>
                  <TableCell className="font-medium">
                    {ticket.subject}
                  </TableCell>
                  <TableCell>{ticket.user.username}</TableCell>
                  <TableCell>
                    <Badge variant={statusVariantMap[ticket.status]}>
                      {tStatus(ticket.status)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={priorityVariantMap[ticket.priority]}>
                      {tPriority(String(ticket.priority))}
                    </Badge>
                  </TableCell>
                  <TableCell>{ticket.assigned_to?.username || "---"}</TableCell>
                  <TableCell>
                    {new Date(ticket.updated_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <TicketActions ticket={ticket} />
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center">
                  {t("table.noResults")}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <DataTablePagination
        pageCount={pageCount}
        currentPage={Number(filters.page)}
        onPageChange={(page) => onFilterChange("page", String(page))}
      />
    </div>
  );
}
