"use client";

import { useState } from "react";
import Sidebar from "@/components/user_layout/UserSidebar";
import UserNavbar from "@/components/user_layout/UserNav";

export default function UserLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <Sidebar isOpen={isOpen} setIsOpen={setIsOpen} />

      <div className="flex flex-1 flex-col">
        {/* Navbar */}
        <UserNavbar isOpen={isOpen} />

        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}
