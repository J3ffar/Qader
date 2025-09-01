"use client";

import React, { forwardRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useAuthCore, useAuthActions } from "@/store/auth.store"; // Adjust path
import { PATHS } from "@/constants/paths"; // Adjust path
import {
  Cog6ToothIcon,
  ExclamationCircleIcon,
  Squares2X2Icon, // Used for Themes heading, not an interactive icon
  QuestionMarkCircleIcon,
  ArrowLeftStartOnRectangleIcon,
} from "@heroicons/react/24/outline"; // Or Lucide equivalents
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useQueryClient } from "@tanstack/react-query";

interface UserProfileDropdownProps {
  isVisible: boolean;
}

const UserProfileDropdown = forwardRef<
  HTMLDivElement,
  UserProfileDropdownProps
>(({ isVisible }, ref) => {
  const router = useRouter();
  const locale = useLocale();
  const { user, isAuthenticated } = useAuthCore();
  const { logout } = useAuthActions();
  const t = useTranslations("Nav.UserDropdown"); // Ensure i18n keys
  const queryClient = useQueryClient();

  if (!isVisible) return null;

  const handleLogout = async () => {
    try {
      await logout(); // This should also handle token removal from Zustand/localStorage via the store action
      queryClient.clear();
      toast.success(t("logoutSuccess"));
      router.push(`/${locale}${PATHS.HOME}`); // Redirect to home on current locale
    } catch (error) {
      console.error("Logout failed:", error);
      toast.error(t("logoutError"));
    }
  };

  const getInitials = (name: string | undefined | null): string => {
    if (!name) return "Q"; // Fallback initial
    return name
      .split(" ")
      .map((n) => n[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  };

  const menuItems = [
    {
      label: t("settings"),
      icon: Cog6ToothIcon,
      href: `/${locale}${PATHS.STUDY.SETTINGS.HOME}`,
    }, // Updated path
 // Updated path
    {
      label: t("adminSupport"),
      icon: QuestionMarkCircleIcon,
      href: `/${locale}${PATHS.STUDY.ADMIN_SUPPORT}`,
    }, // Updated path
  ];

  // Positioning: Typically on the far right.
  const positionClasses = "ltr:right-2 rtl:left-2";

  return (
    <div
      ref={ref}
      className={`absolute top-[calc(100%+8px)] z-50 mt-0 flex w-72 flex-col items-center rounded-2xl border bg-popover text-popover-foreground shadow-lg md:w-80 ${positionClasses}`}
    >
      <div className="flex w-full flex-col items-center border-b py-4">
        {isAuthenticated && !user ? (
          <Skeleton className="h-12 w-12 rounded-full" />
        ) : user ? (
          <Avatar className="h-12 w-12">
            <AvatarImage
              src={user.profile_picture_url || undefined}
              alt={
                user.full_name || user.username || t("userAvatarAltFallback")
              }
            />
            <AvatarFallback>
              {getInitials(user.full_name || user.username)}
            </AvatarFallback>
          </Avatar>
        ) : (
          // Fallback for non-authenticated (should not happen if this dropdown is only for authenticated users)
          <div className="relative h-12 w-12 rounded-full bg-muted" />
        )}

        {isAuthenticated && !user ? (
          <Skeleton className="mt-2 h-5 w-32" />
        ) : user ? (
          <p className="mt-2 text-lg font-medium">
            {user.preferred_name || user.full_name || user.username}
          </p>
        ) : (
          <p className="mt-2 text-lg font-medium">{t("guestUser")}</p>
        )}
      </div>

      <nav className="w-full py-2">
        {menuItems.map((item) => (
          <Button
            asChild
            variant="ghost"
            key={item.label}
            className="w-full justify-start px-4 py-2 text-sm hover:bg-muted"
          >
            <Link href={item.href} className="flex items-center gap-3">
              <item.icon className="h-5 w-5" />
              <span>{item.label}</span>
            </Link>
          </Button>
        ))}

       

        <Button
          variant="ghost"
          className="flex w-full items-center justify-start gap-3 px-4 py-2 text-sm text-destructive hover:bg-red-500/10 hover:text-destructive/90 dark:hover:text-red-400"
          onClick={handleLogout}
        >
          <ArrowLeftStartOnRectangleIcon className="h-5 w-5" />
          <span>{t("logout")}</span>
        </Button>
      </nav>
    </div>
  );
});

UserProfileDropdown.displayName = "UserProfileDropdown";
export default UserProfileDropdown;
