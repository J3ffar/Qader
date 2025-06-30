"use client";

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

        {data?.results.map((ticket) => (
          <TicketListItem
            key={ticket.id}
            ticket={ticket}
            isSelected={ticket.id === selectedTicketId}
          />
        ))}
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

  const createTicketLink = () => {
    const params = new URLSearchParams(searchParams);
    params.set("ticket", String(ticket.id));
    return `${pathname}?${params.toString()}`;
  };

  return (
    <Link
      href={createTicketLink()}
      className={cn(
        "flex flex-col items-start gap-2 rounded-lg border p-3 text-left text-sm transition-all hover:bg-accent",
        isSelected && "bg-muted"
      )}
    >
      <div className="flex w-full items-center justify-between">
        <p className="font-semibold">{ticket.user.username}</p>
        <div
          className={cn(
            "flex items-center justify-center font-medium",
            priorityVariantMap[ticket.priority]
          )}
        >
          <Badge variant={priorityVariantMap[ticket.priority]}>
            P{ticket.priority}
          </Badge>
        </div>
      </div>
      <p className="line-clamp-1 text-xs">{ticket.subject}</p>
      <div className="flex w-full items-center justify-between text-xs text-muted-foreground">
        <p>{ticket.last_reply_by}</p>
        <p>{new Date(ticket.updated_at).toLocaleDateString()}</p>
      </div>
    </Link>
  );
}
