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
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <PlatformSidebar isOpen={isOpen} setIsOpen={setIsOpen} />

      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Navbar */}
        <PlatformHeader isSidebarOpen={isOpen} />

        <div className="sm:p-4 overflow-hidden">{children}</div>
        <WebSocketNotificationHandler />
      </div>
    </div>
  );
}
