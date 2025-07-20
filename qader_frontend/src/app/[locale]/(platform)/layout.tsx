"use client";

import { useState } from "react";
import PlatformHeader from "@/components/features/platform/layout/PlatformHeader";
import PlatformSidebar from "@/components/features/platform/layout/PlatformSidebar";
import { WebSocketNotificationHandler } from "@/components/global/WebSocketNotificationHandler";

export default function UserLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="flex min-h-screen dark:bg-[#081028]">
      {/* Sidebar */}
      <PlatformSidebar isOpen={isOpen} setIsOpen={setIsOpen} />

      <div className="flex flex-1 flex-col">
        {/* Navbar */}
        <PlatformHeader isSidebarOpen={isOpen} />

        <div className="p-4">{children}</div>
        <WebSocketNotificationHandler />
      </div>
    </div>
  );
}
