"use client";

import { Badge } from "@/components/ui/badge";
import type {
  SupportTicketDetail,
  TicketStatus,
} from "@/types/api/support.types";
import { Paperclip, Tag, ShieldQuestion, CircleHelp, Flag } from "lucide-react";

// Reusing status maps from the list view for consistency
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

// Map for issue type icons and text (can be expanded)
const issueTypeMap: Record<string, { text: string; icon: React.ElementType }> =
  {
    technical: { text: "مشكلة تقنية", icon: ShieldQuestion },
    question_problem: { text: "مشكلة في سؤال", icon: CircleHelp },
    suggestion: { text: "اقتراح", icon: Flag },
    inquiry: { text: "استفسار", icon: CircleHelp },
    other: { text: "أخرى", icon: Tag },
  };

interface TicketDetailHeaderProps {
  ticket: SupportTicketDetail;
}

export function TicketDetailHeader({ ticket }: TicketDetailHeaderProps) {
  const issueInfo = issueTypeMap[ticket.issue_type] || issueTypeMap.other;
  const IssueIcon = issueInfo.icon;

  return (
    <header className="p-4 border-b bg-card shrink-0">
      <h1 className="text-xl font-bold">{ticket.subject}</h1>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground mt-2">
        <Badge variant={statusVariantMap[ticket.status]}>
          {statusTextMap[ticket.status]}
        </Badge>

        <div className="flex items-center gap-1.5">
          <IssueIcon className="h-4 w-4" />
          <span>{issueInfo.text}</span>
        </div>

        {ticket.attachment && (
          <a
            href={ticket.attachment}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-primary hover:underline"
          >
            <Paperclip className="h-4 w-4" />
            <span>عرض المرفق</span>
          </a>
        )}
      </div>
    </header>
  );
}
