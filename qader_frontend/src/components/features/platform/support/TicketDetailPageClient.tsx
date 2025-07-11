"use client";

import { useQuery } from "@tanstack/react-query";
import { MessageSquare, ArrowRight } from "lucide-react";
import Link from "next/link";
import { TicketDetailHeader } from "./TicketDetailHeader"; // New Component
import { TicketChatView } from "./TicketChatView";
import { TicketReplyForm } from "./TicketReplyForm";
import { TicketDetailSkeleton } from "./TicketDetailSkeleton";
import { Button } from "@/components/ui/button";
import { queryKeys } from "@/constants/queryKeys";
import { getSupportTicketDetail } from "@/services/support.service";
import { PATHS } from "@/constants/paths";
import { ApiError } from "@/lib/errors";

export function TicketDetailPageClient({ ticketId }: { ticketId: string }) {
  const {
    data: ticket,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: queryKeys.user.support.detail(ticketId),
    queryFn: () => getSupportTicketDetail(ticketId),
    retry: (failureCount, error) => {
      // Don't retry on 404 (Not Found) or 403 (Forbidden) errors
      if (
        error instanceof ApiError &&
        (error.status === 404 || error.status === 403)
      ) {
        return false;
      }
      return failureCount < 3;
    },
  });

  if (isLoading) {
    return <TicketDetailSkeleton />;
  }

  if (isError) {
    let errorMessage = "حدث خطأ أثناء تحميل المحادثة.";
    if (error instanceof ApiError && error.status === 404) {
      errorMessage = "عذراً، لم يتم العثور على تذكرة الدعم هذه.";
    } else if (error instanceof ApiError && error.status === 403) {
      errorMessage = "ليس لديك صلاحية لعرض هذه التذكرة.";
    }

    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <MessageSquare className="w-16 h-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-bold mb-2">خطأ في العرض</h2>
        <p className="text-muted-foreground mb-6">{errorMessage}</p>
        <Button asChild>
          <Link href={PATHS.STUDY.ADMIN_SUPPORT}>
            العودة إلى قائمة الدعم{" "}
            <ArrowRight className="rtl:mr-2 ltr:ml-2 h-4 w-4" />
          </Link>
        </Button>
      </div>
    );
  }

  if (!ticket) {
    // This state should be rare if not loading and not error, but it's a safe fallback.
    return null;
  }

  return (
    // FIX: This is the main container for the chat layout. It's a flex column that takes up 100% of the parent's height.
    <div className="flex flex-col h-full bg-background" dir="rtl">
      {/* The header will not grow or shrink */}
      <TicketDetailHeader ticket={ticket} />

      {/* This container will grow to fill the space and provides the boundary for the scrollable area */}
      <div className="flex-1 min-h-0">
        <TicketChatView ticket={ticket} />
      </div>

      {/* The reply form will not grow or shrink */}
      <div className="shrink-0">
        <TicketReplyForm
          ticketId={ticketId}
          isTicketClosed={ticket.status === "closed"}
        />
      </div>
    </div>
  );
}
