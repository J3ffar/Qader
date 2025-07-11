import { TicketDetailPageClient } from "@/components/features/platform/support/TicketDetailPageClient";

interface TicketDetailPageProps {
  params: Promise<{
    local: string;
    ticketId: string;
  }>;
}

// This page is dynamic, so we render the client component directly.
export default async function TicketDetailPage({
  params,
}: TicketDetailPageProps) {
  // The client component will handle all fetching, state management, and UI.
  return <TicketDetailPageClient ticketId={(await params).ticketId} />;
}
