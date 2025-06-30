"use client";

import { useSearchParams } from "next/navigation";
import { TicketList } from "./TicketList";
import { TicketDetail } from "./TicketDetail";

export function SupportInboxLayout() {
  const searchParams = useSearchParams();
  const activeTab = searchParams.get("tab") || "all";
  const selectedTicketId = searchParams.get("ticket");

  return (
    <div className="flex-1 grid grid-cols-1 md:grid-cols-[350px_1fr] border-t h-0">
      {/* Ticket List Pane */}
      <aside className="border-r overflow-y-auto">
        <TicketList
          activeTab={activeTab}
          selectedTicketId={selectedTicketId ? Number(selectedTicketId) : null}
        />
      </aside>

      {/* Ticket Detail Pane */}
      <main className="overflow-y-auto">
        <TicketDetail
          key={selectedTicketId} // Re-mount component on ticket change for clean state
          ticketId={selectedTicketId ? Number(selectedTicketId) : null}
        />
      </main>
    </div>
  );
}
