"use client";

import { useState } from "react";
import Sidebar from "./sidbar/page";
import UserNavbar from "./nav/page";

export default function UserLayout({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <Sidebar isOpen={isOpen} setIsOpen={setIsOpen} />

      <div className="flex flex-col flex-1">
        {/* Navbar */}
        <UserNavbar isOpen={isOpen} />

        <div className="p-4 mt-[80px]">
          {children}
        </div>
      </div>
    </div>
  );
}
