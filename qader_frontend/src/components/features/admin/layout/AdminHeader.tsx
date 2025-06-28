"use client";

import { useTranslations } from "next-intl";
import {
  Bell,
  ChevronDown,
  LogOut,
  Search,
  Settings,
  UserCircle,
} from "lucide-react";
import { useAuthCore, useAuthStore } from "@/store/auth.store";
import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/constants/queryKeys";
import { getNotifications } from "@/services/notification.service";
import NotificationsDropdown from "@/components/features/platform/layout/platform-header/NotificationsDropdown";
import { useState, useRef } from "react";
import { useOnClickOutside } from "@/hooks/useOnClickOutside";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Input } from "@/components/ui/input";
import { useAuthActions } from "@/store/auth.store";
import { PATHS } from "@/constants/paths";
import { toast } from "sonner";

const getInitials = (name: string | undefined | null): string => {
  if (!name) return "A";
  return name
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
};

const AdminHeader = () => {
  const t = useTranslations("Nav.AdminHeader");
  const { user, isAuthenticated } = useAuthCore();
  const { logout } = useAuthActions();
  const router = useRouter();
  const { updateUserProfile } = useAuthStore();

  const [isNotificationsDropdownOpen, setIsNotificationsDropdownOpen] =
    useState(false);
  const notificationsTriggerRef = useRef<HTMLButtonElement>(null);
  const notificationsDropdownRef = useRef<HTMLDivElement>(null);

  useOnClickOutside(
    notificationsDropdownRef,
    notificationsTriggerRef,
    () => setIsNotificationsDropdownOpen(false),
    isNotificationsDropdownOpen
  );

  const { data: notificationsCountResponse } = useQuery({
    queryKey: queryKeys.notifications.unreadCount(),
    queryFn: () => getNotifications({ is_read: false, pageSize: 1 }),
    enabled: isAuthenticated,
    staleTime: 1000 * 60 * 5, // 5 minutes
    select: (data) => data.count,
  });

  // Update Zustand store with the latest unread count
  if (
    isAuthenticated &&
    user &&
    notificationsCountResponse !== undefined &&
    notificationsCountResponse !== user.unread_notifications_count
  ) {
    updateUserProfile({
      unread_notifications_count: notificationsCountResponse,
    });
  }

  const handleLogout = async () => {
    try {
      await logout();
      toast.success(t("logoutSuccess"));
      router.push(PATHS.HOME);
    } catch (error) {
      console.error("Logout failed:", error);
      toast.error(t("logoutError"));
    }
  };

  return (
    <header className="sticky top-0 z-30 flex h-20 w-full items-center justify-between border-b bg-background px-6">
      {/* Center - Search Bar */}
      <div className="relative w-full max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3 rtl:left-auto" />
        <Input
          type="search"
          placeholder={t("searchPlaceholder")}
          className="w-full bg-muted pl-9 rtl:pr-9"
        />
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center">
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "relative rounded-xl border w-10 h-10",
              isNotificationsDropdownOpen
                ? "bg-muted dark:bg-muted/50"
                : "hover:bg-muted dark:hover:bg-muted/50"
            )}
            onClick={() =>
              setIsNotificationsDropdownOpen(!isNotificationsDropdownOpen)
            }
            ref={notificationsTriggerRef}
          >
            <Bell className="h-6 w-6" />
            {isAuthenticated && user && user.unread_notifications_count > 0 && (
              <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                {user.unread_notifications_count > 9
                  ? "9+"
                  : user.unread_notifications_count}
              </span>
            )}
            {isAuthenticated && !user && (
              <Skeleton className="absolute -right-1 -top-1 h-5 w-5 rounded-full" />
            )}
          </Button>
          {isNotificationsDropdownOpen && (
            <NotificationsDropdown
              ref={notificationsDropdownRef}
              isVisible={true}
            />
          )}
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="flex h-auto items-center gap-3 p-1 border rounded-xl"
            >
              <div className="relative">
                <Avatar className="h-12 w-12">
                  <AvatarImage
                    src={user?.profile_picture_url || ""}
                    alt={user?.full_name || "Admin"}
                  />
                  <AvatarFallback>
                    {getInitials(user?.full_name)}
                  </AvatarFallback>
                </Avatar>
                <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background bg-green-500" />
              </div>
              <div className="hidden flex-col items-start text-start md:flex">
                <span className="font-semibold">
                  {user?.full_name || "Admin User"}
                </span>
                <span className="text-sm text-muted-foreground">
                  {t("greeting")}
                </span>
              </div>
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="start" forceMount>
            <DropdownMenuLabel>{t("myAccount")}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href={PATHS.ADMIN.PROFILE}>
                <UserCircle className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
                <span>{t("profile")}</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href={PATHS.ADMIN.SETTINGS}>
                <Settings className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
                <span>{t("settings")}</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive focus:bg-destructive/10 focus:text-destructive"
              onClick={handleLogout}
            >
              <LogOut className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
              <span>{t("logout")}</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

export default AdminHeader;
