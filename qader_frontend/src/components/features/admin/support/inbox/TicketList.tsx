import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Mail, Inbox } from "lucide-react";

import { queryKeys } from "@/constants/queryKeys";
import { getSupportTickets } from "@/services/api/admin/support.service";
import type {
  TicketIssueType,
  SupportTicketListItem,
} from "@/types/api/admin/support.types";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { TicketListSkeleton } from "./TicketListSkeleton";

const issueTypes: (TicketIssueType | "all")[] = [
  "all",
  "technical",
  "question_problem",
  "suggestion",
  "inquiry",
  "other",
];

const priorityVariantMap: Record<
  number,
  "destructive" | "default" | "secondary"
> = {
  1: "destructive",
  2: "default",
  3: "secondary",
};

export function TicketList({
  activeTab,
  selectedTicketId,
}: {
  activeTab: string;
  selectedTicketId: number | null;
}) {
  const t = useTranslations("Admin.support");
  const tIssue = useTranslations("Admin.support.issueTypeLabels");
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.admin.support.list({
      issue_type: activeTab === "all" ? undefined : activeTab,
      ordering: "-updated_at",
    }),
    queryFn: () =>
      getSupportTickets({
        issue_type: activeTab === "all" ? undefined : activeTab,
        ordering: "-updated_at",
      }),
  });

  const createTabLink = (tab: string) => {
    const params = new URLSearchParams(searchParams);
    params.set("tab", tab);
    params.delete("ticket"); // Clear selected ticket when changing tabs
    return `${pathname}?${params.toString()}`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="p-2 border-b">
        <nav className="flex flex-col gap-1">
          {issueTypes.map((tab) => (
            <Link
              key={tab}
              href={createTabLink(tab)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary",
                activeTab === tab && "bg-muted text-primary"
              )}
            >
              <Mail className="h-4 w-4" />
              {tIssue(tab)}
            </Link>
          ))}
        </nav>
      </div>

      {/* Ticket List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && <TicketListSkeleton />}
        {isError && (
          <div className="p-4 text-center text-destructive">
            {t("errors.fetchError")}
          </div>
        )}

        {data && data.results.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground p-4">
            <Inbox className="h-12 w-12 mb-2" />
            <p className="font-semibold">{t("inbox.noTicketsTitle")}</p>
            <p className="text-sm">{t("inbox.noTicketsDescription")}</p>
          </div>
        )}

        <div className="flex flex-col">
          {data?.results.map((ticket) => (
            <TicketListItem
              key={ticket.id}
              ticket={ticket}
              isSelected={ticket.id === selectedTicketId}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function TicketListItem({
  ticket,
  isSelected,
}: {
  ticket: SupportTicketListItem;
  isSelected: boolean;
}) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const tPriority = useTranslations("Admin.support.priorityLabels");

  const createTicketLink = () => {
    const params = new URLSearchParams(searchParams);
    params.set("ticket", String(ticket.id));
    return `${pathname}?${params.toString()}`;
  };

  return (
    <Link
      href={createTicketLink()}
      className={cn(
        "flex flex-col items-start gap-2 rounded-lg border-b p-3 text-left text-sm transition-all hover:bg-accent m-2",
        isSelected && "bg-muted"
      )}
    >
      <div className="flex w-full items-center">
        <p className="font-semibold flex-1 truncate">
          {ticket.user.full_name || ticket.user.username}
        </p>
        <Badge variant={priorityVariantMap[ticket.priority]}>
          {tPriority(String(ticket.priority))}
        </Badge>
      </div>
      <p className="font-semibold line-clamp-1 text-sm">{ticket.subject}</p>
      <div className="flex w-full items-center justify-between text-xs text-muted-foreground">
        <p>الرد الأخير: {ticket.last_reply_by}</p>
        <p>{new Date(ticket.updated_at).toLocaleDateString()}</p>
      </div>
    </Link>
  );
}
