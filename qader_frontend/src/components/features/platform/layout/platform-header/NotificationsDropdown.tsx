"use client";

import React, { forwardRef } from "react"; // Added forwardRef
import Image from "next/image";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  getNotifications,
  markAllNotificationsAsRead,
} from "@/services/notification.service"; // Path might need adjustment
import type { Notification } from "@/types/api/notification.types"; // Path might need adjustment
import { useAuthStore } from "@/store/auth.store"; // Path might need adjustment
import { queryKeys } from "@/constants/queryKeys";

interface NotificationsDropdownProps {
  isVisible: boolean;
}

// If useOnClickOutside needs to target the root of THIS component, it needs to forward a ref.
const NotificationsDropdown = forwardRef<
  HTMLDivElement,
  NotificationsDropdownProps
>(({ isVisible }, ref) => {
  const t = useTranslations("Nav.PlatformHeader.NotificationsDropdown"); // Ensure i18n keys are correct
  const queryClient = useQueryClient();
  const { user, updateUserProfile } = useAuthStore();

  const {
    data: notificationsResponse,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.notifications.list({
      pageSize: 5,
      ordering: "-created_at_iso",
    }),
    queryFn: () =>
      getNotifications({ pageSize: 5, ordering: "-created_at_iso" }),
    enabled: isVisible, // Only fetch when the dropdown is visible
    staleTime: 1000 * 60 * 2, // 2 minutes
  });

  const markAllReadMutation = useMutation({
    mutationFn: markAllNotificationsAsRead,
    onSuccess: (data) => {
      toast.success(data.detail || t("allReadSuccess"));
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.unreadCount(),
      });
      if (user) {
        updateUserProfile({ unread_notifications_count: 0 });
      }
    },
    onError: () => {
      toast.error(t("allReadError"));
    },
  });

  if (!isVisible) return null;

  const notifications = notificationsResponse?.results || [];

  const handleMarkAllRead = () => {
    markAllReadMutation.mutate();
  };

  const renderNotificationItem = (notification: Notification) => (
    <Link
      href={notification.url || "#"}
      key={notification.id}
      passHref
      legacyBehavior // Consider removing if not strictly needed for styling an <a> tag.
    >
      <a className="block rounded-md border-t border-border px-2 py-3 transition-colors hover:bg-muted dark:hover:bg-muted/50">
        <div className="flex items-start justify-between gap-2">
          <Image
            src={
              notification.actor?.profile_picture_url || "/images/logoside.png"
            }
            width={42}
            height={42}
            alt={
              notification.actor?.full_name || t("notificationActorAltFallback")
            }
            className="rounded-full border"
          />
          <div className="flex-1 ltr:text-left rtl:text-right">
            <p className="text-sm font-semibold">{notification.verb}</p>
            {notification.description && (
              <p className="max-w-xs text-xs text-muted-foreground">
                {notification.description}
              </p>
            )}
          </div>
        </div>
        <span className="mt-1 block text-right text-xs text-muted-foreground">
          {notification.timesince ||
            new Date(notification.created_at_iso).toLocaleTimeString()}
        </span>
      </a>
    </Link>
  );

  const renderSkeletonItem = (
    key: number // Added key for mapped items
  ) => (
    <div key={key} className="border-t border-border px-2 py-3">
      <div className="flex items-center gap-2">
        <Skeleton className="h-[30px] w-[30px] rounded-full" />
        <div className="flex-1 space-y-1">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <Skeleton className="ml-auto mt-1 h-3 w-1/4" />
    </div>
  );

  return (
    <div
      ref={ref} // Apply forwarded ref here
      // The className "bellshap" was likely for targeting this specific element.
      // More semantic classNames or data-attributes could be used if needed.
      // Positioning "absolute top-[70px]" needs to be relative to PlatformHeader.
      // Consider using Shadcn Popover or DropdownMenu components for better accessibility and positioning.
      className="absolute top-[calc(100%+8px)] z-50 w-80 rounded-2xl border bg-popover p-4 text-popover-foreground shadow-lg ltr:right-0 rtl:left-0 md:left-auto md:w-96"
      // Example if this was directly under the bell icon:
      // className="... absolute top-full z-50 mt-2 w-80 ltr:right-0 rtl:left-auto" (if bell icon is on the right)
    >
      <div className="flex items-center justify-between px-2 py-3">
        <p className="font-bold">{t("title")}</p>
        {notifications.length > 0 && (
          <Button
            variant="link"
            size="sm"
            className="h-auto p-0 text-xs text-primary"
            onClick={handleMarkAllRead}
            disabled={markAllReadMutation.isPending}
          >
            {markAllReadMutation.isPending ? t("marking") : t("markAllRead")}
          </Button>
        )}
      </div>

      <ScrollArea className="h-[300px] pr-2">
        {isLoading &&
          Array.from({ length: 3 }).map((_, index) =>
            renderSkeletonItem(index)
          )}
        {!isLoading && !isError && notifications.length === 0 && (
          <p className="py-10 text-center text-muted-foreground">
            {t("noNotifications")}
          </p>
        )}
        {isError && (
          <p className="py-10 text-center text-destructive">
            {t("errorLoading")}
          </p>
        )}
        {!isLoading && !isError && notifications.map(renderNotificationItem)}
      </ScrollArea>
      <div className="mt-2 border-t border-border pt-2 text-center">
        <Button asChild variant="ghost" size="sm" className="w-full">
          <Link href="/notifications">{t("viewAll")}</Link>
        </Button>
      </div>
    </div>
  );
});

NotificationsDropdown.displayName = "NotificationsDropdown";

export default NotificationsDropdown;
