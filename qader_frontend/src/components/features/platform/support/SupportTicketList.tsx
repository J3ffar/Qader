// src/components/features/platform/support/SupportTicketList.tsx
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PATHS } from "@/constants/paths";
import type {
  SupportTicketList as Ticket,
  TicketStatus,
} from "@/types/api/support.types";
import { format } from "date-fns";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

const statusVariantMap: Record<
  TicketStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  open: "default",
  pending_admin: "default",
  pending_user: "outline",
  closed: "secondary",
};

const statusTextMap: Record<TicketStatus, string> = {
  open: "مفتوحة",
  pending_admin: "قيد المراجعة",
  pending_user: "بانتظار ردك",
  closed: "مغلقة",
};

export function SupportTicketList({ tickets }: { tickets: Ticket[] }) {
  if (tickets.length === 0) {
    return (
      <p className="text-center text-muted-foreground py-8">
        لا يوجد لديك تذاكر دعم سابقة.
      </p>
    );
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>التاريخ</TableHead>
          <TableHead>الحالة</TableHead>
          <TableHead>الموضوع</TableHead>
          <TableHead></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tickets.map((ticket) => (
          <TableRow key={ticket.id}>
            <TableCell>
              {format(new Date(ticket.created_at), "yyyy/MM/dd")}
            </TableCell>
            <TableCell>
              <Badge variant={statusVariantMap[ticket.status]}>
                {statusTextMap[ticket.status]}
              </Badge>
            </TableCell>
            <TableCell className="font-medium">{ticket.subject}</TableCell>
            <TableCell>
              <Link
                href={`${PATHS.STUDY.ADMIN_SUPPORT}/${ticket.id}`}
                className="flex items-center text-primary hover:underline"
              >
                عرض <ArrowLeft className="h-4 w-4 rtl:mr-1 ltr:ml-1" />
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
