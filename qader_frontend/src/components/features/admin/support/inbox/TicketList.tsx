"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Inbox } from "lucide-react";

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
      // This logic is correct: when activeTab is "all", `issue_type` is undefined.
      // TanStack Query automatically omits undefined keys from the request.
      issue_type: activeTab === "all" ? "" : activeTab,
      ordering: "-updated_at",
    }),
    queryFn: () =>
      getSupportTickets({
        issue_type: activeTab === "all" ? "" : activeTab,
        ordering: "-updated_at",
      }),
  });

  const createTabLink = (tab: string) => {
    const params = new URLSearchParams(searchParams);
    params.set("tab", tab);
    params.delete("ticket");
    return `${pathname}?${params.toString()}`;
  };

  return (
    // This structure ensures the tabs are fixed and the list below scrolls
    <div className="flex flex-col h-full">
      {/* Horizontal Scrollable Tabs */}
      <div className="flex-shrink-0 p-2 border-b">
        <div className="overflow-x-auto pb-2">
          <nav className="flex space-x-2 rtl:space-x-reverse">
            {issueTypes.map((tab) => (
              <Link
                key={tab}
                href={createTabLink(tab)}
                className={cn(
                  "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                  "flex-shrink-0", // Prevents tabs from shrinking
                  activeTab === tab
                    ? "bg-primary text-primary-foreground shadow"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                {tIssue(tab)}
              </Link>
            ))}
          </nav>
        </div>
      </div>

      {/* Scrollable Ticket List Area */}
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

// TicketListItem remains the same as in the previous improvement.
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
  const tIssue = useTranslations("Admin.support.issueTypeLabels");

  const createTicketLink = () => {
    const params = new URLSearchParams(searchParams);
    params.set("ticket", String(ticket.id));
    return `${pathname}?${params.toString()}`;
  };

  return (
    <Link
      href={createTicketLink()}
      className={cn(
        "flex flex-col items-start gap-2 border-b p-3 text-left text-sm transition-all hover:bg-accent",
        isSelected ? "bg-muted" : "bg-transparent"
      )}
    >
      <div className="flex w-full items-center gap-2">
        <p className="font-semibold flex-1 truncate">
          {ticket.user.full_name || ticket.user.username}
        </p>
        <Badge variant={priorityVariantMap[ticket.priority]}>
          {tPriority(String(ticket.priority))}
        </Badge>
        {ticket.issue_type && (
          <Badge variant="secondary" className="flex-shrink-0">
            {tIssue(ticket.issue_type)}
          </Badge>
        )}
      </div>
      <p className="font-semibold line-clamp-1 text-sm">{ticket.subject}</p>
      <div className="flex w-full items-center justify-between text-xs text-muted-foreground">
        <p>الرد الأخير: {ticket.last_reply_by}</p>
        <p>{new Date(ticket.updated_at).toLocaleDateString()}</p>
      </div>
    </Link>
  );
}
