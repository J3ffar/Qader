"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CheckIcon, TrashIcon } from "lucide-react";
import {
  getNotifications,
  markAllNotificationsAsRead,
  markNotificationAsRead,
  deleteNotification,
} from "@/services/notification.service";
import type { Notification } from "@/types/api/notification.types";
import { useAuthStore } from "@/store/auth.store";
import { queryKeys } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";

export default function NotificationsPage() {
  const t = useTranslations("Notifications");
  const queryClient = useQueryClient();
  const { user, updateUserProfile } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"all" | "unread" | "read">("all");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const {
    data: notificationsResponse,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: queryKeys.notifications.list({
      pageSize,
      page,
      ordering: "-created_at_iso",
      ...(activeTab === "unread" && { is_read: false }),
      ...(activeTab === "read" && { is_read: true }),
    }),
    queryFn: () =>
      getNotifications({
        pageSize,
        page,
        ordering: "-created_at_iso",
        ...(activeTab === "unread" && { is_read: false }),
        ...(activeTab === "read" && { is_read: true }),
      }),
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
      refetch();
    },
    onError: () => {
      toast.error(t("allReadError"));
    },
  });

  const markReadMutation = useMutation({
    mutationFn: ({ id }: { id: number }) => markNotificationAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.unreadCount(),
      });
      refetch();
    },
    onError: () => {
      toast.error(t("markReadError"));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ({ id }: { id: number }) => deleteNotification(id),
    onSuccess: () => {
      toast.success(t("deleteSuccess"));
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.unreadCount(),
      });
      refetch();
    },
    onError: () => {
      toast.error(t("deleteError"));
    },
  });

  const handleMarkAllRead = () => {
    markAllReadMutation.mutate();
  };

  const handleMarkRead = (id: number) => {
    markReadMutation.mutate({ id });
  };

  const handleDelete = (id: number) => {
    deleteMutation.mutate({ id });
  };

  const notifications = notificationsResponse?.results || [];
  const totalPages = Math.ceil((notificationsResponse?.count || 0) / pageSize);

  const renderNotificationItem = (notification: Notification) => (
    <div
      key={notification.id}
      className={`flex items-start gap-4 p-4 rounded-lg border transition-colors max-w-5xl mx-auto ${
        notification.is_read ? "bg-muted/30" : "bg-background border-primary/20"
      }`}
    >
      <Image
        src={notification.actor?.profile_picture_url || "/images/logoside.png"}
        width={48}
        height={48}
        alt={notification.actor?.full_name || t("notificationActorAltFallback")}
        className="rounded-full border flex-shrink-0"
      />

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <p className="text-sm font-semibold">{notification.verb}</p>
            {notification.description && (
              <p className="text-sm text-muted-foreground mt-1">
                {notification.description}
              </p>
            )}
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-muted-foreground">
                {notification.timesince ||
                  new Date(notification.created_at_iso).toLocaleString()}
              </span>
              {!notification.is_read && (
                <Badge variant="secondary" className="text-xs">
                  {t("unread")}
                </Badge>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1">
            {!notification.is_read && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleMarkRead(notification.id)}
                disabled={markReadMutation.isPending}
                className="h-8 w-8 p-0"
              >
                <CheckIcon className="h-4 w-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleDelete(notification.id)}
              disabled={deleteMutation.isPending}
              className="h-8 w-8 p-0 text-destructive hover:text-destructive"
            >
              <TrashIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>
        {notification.url && notification.url !== "#" && (
          <div className="mt-2">
            <Button asChild variant="outline" size="sm">
              <Link href={notification.url}>{t("viewDetails")}</Link>
            </Button>
          </div>
        )}
      </div>
    </div>
  );

  const renderSkeletonItem = (key: number) => (
    <div key={key} className="flex items-start gap-4 p-4 rounded-lg border">
      <Skeleton className="h-12 w-12 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-3 w-1/4" />
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>
        <p className="text-muted-foreground">{t("description")}</p>
      </header>

      <div className="flex items-center justify-between">
        <Tabs
          value={activeTab}
          onValueChange={(value) => {
            setActiveTab(value as "all" | "unread" | "read");
            setPage(1);
          }}
        >
          <TabsList>
            <TabsTrigger value="all" className="cursor-pointer">
              {t("tabs.all")}
            </TabsTrigger>
            <TabsTrigger value="unread" className="cursor-pointer">
              {t("tabs.unread")}
            </TabsTrigger>
            <TabsTrigger value="read" className="cursor-pointer">
              {t("tabs.read")}
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {activeTab === "unread" && notifications.length > 0 && (
          <Button
            variant="outline"
            onClick={handleMarkAllRead}
            disabled={markAllReadMutation.isPending}
          >
            {markAllReadMutation.isPending ? t("marking") : t("markAllRead")}
          </Button>
        )}
      </div>

      <Separator />

      <div className="space-y-4">
        {isLoading &&
          Array.from({ length: 5 }).map((_, index) =>
            renderSkeletonItem(index)
          )}

        {!isLoading && !isError && notifications.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground text-lg">
              {activeTab === "all" && t("noNotifications")}
              {activeTab === "unread" && t("noUnreadNotifications")}
              {activeTab === "read" && t("noReadNotifications")}
            </p>
          </div>
        )}

        {isError && (
          <div className="text-center py-12">
            <p className="text-destructive text-lg">{t("errorLoading")}</p>
            <Button
              variant="outline"
              onClick={() => refetch()}
              className="mt-4"
            >
              {t("retry")}
            </Button>
          </div>
        )}

        {!isLoading && !isError && notifications.map(renderNotificationItem)}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(page - 1)}
            disabled={page <= 1}
          >
            {t("previous")}
          </Button>

          <span className="text-sm text-muted-foreground">
            {t("pageInfo", { current: page, total: totalPages })}
          </span>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(page + 1)}
            disabled={page >= totalPages}
          >
            {t("next")}
          </Button>
        </div>
      )}
    </div>
  );
}
