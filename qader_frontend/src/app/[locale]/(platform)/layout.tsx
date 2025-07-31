"use client";

import PlatformHeader from "@/components/features/platform/layout/PlatformHeader";
import PlatformSidebar from "@/components/features/platform/layout/PlatformSidebar";
import { WebSocketNotificationHandler } from "@/components/global/WebSocketNotificationHandler";
import { useState } from "react";

export default function UserLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="flex h-screen bg-muted/40">
      {/* Sidebar */}
      <PlatformSidebar isOpen={isOpen} setIsOpen={setIsOpen} />

      <div className="flex flex-1 flex-col">
        {/* Navbar */}
        <PlatformHeader isSidebarOpen={isOpen} />

        <main className="flex-1 overflow-y-auto p-4">{children}</main>
        <WebSocketNotificationHandler />
      </div>
    </div>
  );
}
