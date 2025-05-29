"use client";

import React from "react";
import { useRouter } from "next/navigation"; // For redirection
import { useLocale } from "next-intl";
import { toast } from "sonner"; // For notifications
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button"; // For logout button
import { ThemesToggles } from "@/components/ui/ThemesToggle"; // Assuming this is your dark mode toggle
import { useAuthCore, useAuthActions } from "@/store/auth.store";
import { PATHS } from "@/constants/paths";

import {
  Cog6ToothIcon,
  ExclamationCircleIcon,
  Squares2X2Icon,
  QuestionMarkCircleIcon,
  ArrowLeftStartOnRectangleIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link"; // For navigation links

interface UserContainProps {
  showUserContain: boolean;
}

const UserContain = ({ showUserContain }: UserContainProps) => {
  const router = useRouter();
  const locale = useLocale();
  const { user, isAuthenticated } = useAuthCore();
  const { logout } = useAuthActions();
  // Add translations if needed for menu items
  // const t = useTranslations("UserDropdown");

  if (!showUserContain) return null;

  const handleLogout = async () => {
    try {
      await logout();
      toast.success("تم تسجيل الخروج بنجاح!"); // "Logged out successfully!"
      router.push(`/${locale}${PATHS.LOGIN}`);
    } catch (error) {
      console.error("Logout failed:", error);
      toast.error("فشل تسجيل الخروج. حاول مرة أخرى."); // "Logout failed. Please try again."
    }
  };

  const getInitials = (name: string | undefined | null): string => {
    if (!name) return "Q";
    return name
      .split(" ")
      .map((n) => n[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  };

  const menuItems = [
    {
      label: "الإعدادات", // t("settings")
      icon: Cog6ToothIcon,
      href: `/${locale}${PATHS.STUDY_HOME}/settings`, // Example path
    },
    {
      label: "وضع الطوارئ", // t("emergencyMode")
      icon: ExclamationCircleIcon,
      href: `/${locale}${PATHS.STUDY_HOME}/emergency-mode`, // Example path
    },
    // Theme toggle is separate
    {
      label: "الدعم الإدارى", // t("adminSupport")
      icon: QuestionMarkCircleIcon,
      href: `/${locale}${PATHS.STUDY_HOME}/admin-support`, // Example path
    },
  ];

  return (
    <div className="Usercontain absolute left-2 top-16 z-50 mt-2 flex w-72 flex-col items-center rounded-2xl border bg-popover text-popover-foreground shadow-lg md:w-80">
      <div className="flex w-full flex-col items-center border-b py-4">
        {isAuthenticated && !user ? (
          <Skeleton className="h-12 w-12 rounded-full" />
        ) : user ? (
          <Avatar className="h-12 w-12">
            <AvatarImage
              src={user.profile_picture_url || undefined}
              alt={user.full_name || user.username || "User"}
            />
            <AvatarFallback>
              {getInitials(user.full_name || user.username)}
            </AvatarFallback>
            {/* Online status indicator - can be conditional */}
            <span className="absolute right-0 top-1 h-3 w-3 rounded-full border-2 border-popover bg-green-500"></span>
          </Avatar>
        ) : (
          <div className="relative h-12 w-12 rounded-full bg-muted">
            <span className="absolute right-0 top-1 h-3 w-3 rounded-full border-2 border-white bg-green-500"></span>
          </div>
        )}

        {isAuthenticated && !user ? (
          <Skeleton className="mt-2 h-5 w-32" />
        ) : user ? (
          <p className="mt-2 text-lg font-medium">
            {user.preferred_name || user.full_name || user.username}
          </p>
        ) : (
          <p className="mt-2 text-lg font-medium">زائر</p> // "Guest"
        )}
      </div>

      <nav className="w-full py-2">
        {menuItems.map((item) => (
          <Link href={item.href} key={item.label} passHref>
            <Button
              variant="ghost"
              className="flex w-full items-center justify-start gap-3 px-4 py-2 text-sm hover:bg-muted"
            >
              <item.icon className="h-5 w-5" />
              <span>{item.label}</span>
            </Button>
          </Link>
        ))}

        <div className="flex w-full items-center justify-between gap-2 border-b border-t px-4 py-3 text-sm">
          <p className="flex items-center gap-3">
            <Squares2X2Icon className="h-5 w-5" /> السمات {/* t("themes") */}
          </p>
          <ThemesToggles />
        </div>

        <Button
          variant="ghost"
          className="flex w-full items-center justify-start gap-3 px-4 py-2 text-sm text-red-600 hover:bg-red-500/10 hover:text-red-700 dark:text-red-500 dark:hover:text-red-400"
          onClick={handleLogout}
        >
          <ArrowLeftStartOnRectangleIcon className="h-5 w-5" />
          <span>تسجيل خروج</span> {/* t("logout") */}
        </Button>
      </nav>
    </div>
  );
};

export default UserContain;
