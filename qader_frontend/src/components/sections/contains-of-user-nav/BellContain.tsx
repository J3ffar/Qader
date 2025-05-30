"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area"; // For scrollable notifications
import {
  getNotifications,
  markAllNotificationsAsRead,
} from "@/services/notification.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import type { Notification } from "@/types/api/notification.types";
import { useAuthStore } from "@/store/auth.store"; // To update user's unread count

const BellShap = ({ showBellDropdown }: { showBellDropdown: boolean }) => {
  const t = useTranslations("Nav.UserNav.BellDropdown");
  const queryClient = useQueryClient();
  const { user, updateUserProfile } = useAuthStore(); // Get setUser to update unread_notifications_count

  const {
    data: notificationsResponse,
    isLoading,
    isError,
  } = useQuery({
    queryKey: [
      QUERY_KEYS.NOTIFICATIONS_LIST,
      { pageSize: 5, ordering: "-created_at_iso" },
    ],
    queryFn: () =>
      getNotifications({ pageSize: 5, ordering: "-created_at_iso" }),
    enabled: showBellDropdown, // Only fetch when the dropdown is visible
    staleTime: 1000 * 60 * 2, // 2 minutes
  });

  const markAllReadMutation = useMutation({
    mutationFn: markAllNotificationsAsRead,
    onSuccess: (data) => {
      toast.success(data.detail || t("allReadSuccess"));
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.NOTIFICATIONS_LIST],
      });
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.NOTIFICATIONS_UNREAD_COUNT],
      });
      // Update user profile in Zustand store
      if (user) {
        updateUserProfile({ unread_notifications_count: 0 });
      }
    },
    onError: () => {
      toast.error(t("allReadError"));
    },
  });

  if (!showBellDropdown) return null;

  const notifications = notificationsResponse?.results || [];

  const handleMarkAllRead = () => {
    markAllReadMutation.mutate();
  };

  const renderNotificationItem = (notification: Notification) => (
    <Link
      href={notification.url || "#"}
      key={notification.id}
      passHref
      legacyBehavior
    >
      <a className="block rounded-md border-t border-border px-2 py-3 transition-colors hover:bg-muted dark:hover:bg-muted/50">
        <div className="flex items-start justify-between gap-2">
          {/* You might want a generic notification icon or one based on notification.actor.profile_picture_url */}
          <Image
            src={
              notification.actor?.profile_picture_url || "/images/logoside.png"
            } // Fallback icon
            width={42}
            height={42}
            alt={notification.actor?.full_name || "Notification"}
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

  const renderSkeletonItem = () => (
    <div className="border-t border-border px-2 py-3">
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
    <div className="bellshap absolute top-[70px] z-50 w-80 rounded-2xl border bg-popover p-4 text-popover-foreground shadow-lg ltr:right-0 rtl:left-0 md:left-auto md:w-96">
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
        {" "}
        {/* Adjust height as needed */}
        {isLoading &&
          Array.from({ length: 3 }).map((_, index) => renderSkeletonItem())}
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
        <Link href="/notifications" passHref legacyBehavior>
          <Button variant="ghost" size="sm" className="w-full">
            {t("viewAll")}
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default BellShap;
