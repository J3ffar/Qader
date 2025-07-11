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
  return (
    // This container is crucial. It sets the boundary for the flex layout inside the client component.
    <div className="h-[calc(100vh-105px)]">
      <TicketDetailPageClient ticketId={(await params).ticketId} />
    </div>
  );
}
