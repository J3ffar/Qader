"use client";

import { useSearchParams } from "next/navigation";
import { useMediaQuery } from "@/hooks/use-media-query";
import { cn } from "@/lib/utils";
import { TicketList } from "./TicketList";
import { TicketDetail } from "./TicketDetail";
import { SelectTicketPlaceholder } from "./TicketDetail"; // Import the placeholder

export function SupportInboxLayout() {
  const searchParams = useSearchParams();
  const isMobile = useMediaQuery("(max-width: 768px)"); // md breakpoint

  const activeTab = searchParams.get("tab") || "all";
  const selectedTicketId = searchParams.get("ticket");

  const showList = !isMobile || (isMobile && !selectedTicketId);
  const showDetail = !isMobile || (isMobile && selectedTicketId);

  return (
    <div className="flex-1 grid md:grid-cols-[350px_1fr] border-t h-0">
      {/* Ticket List Pane */}
      <aside className={cn("border-r overflow-y-auto", !showList && "hidden")}>
        <TicketList
          activeTab={activeTab}
          selectedTicketId={selectedTicketId ? Number(selectedTicketId) : null}
        />
      </aside>

      {/* Ticket Detail Pane */}
      <main className={cn("overflow-y-auto", !showDetail && "hidden")}>
        {selectedTicketId ? (
          <TicketDetail
            key={selectedTicketId} // Re-mount component on ticket change for clean state
            ticketId={Number(selectedTicketId)}
          />
        ) : (
          // Only show placeholder on desktop when no ticket is selected
          !isMobile && <SelectTicketPlaceholder />
        )}
      </main>
    </div>
  );
}
