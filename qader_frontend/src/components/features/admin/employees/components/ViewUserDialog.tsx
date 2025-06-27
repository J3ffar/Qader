"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations, useFormatter } from "next-intl";
import { getAdminUserDetail } from "@/services/api/admin/users.service";
import { queryKeys } from "@/constants/queryKeys";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

interface ViewUserDialogProps {
  userId: number | null;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const DetailRow = ({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) => (
  <div className="grid grid-cols-3 gap-4 py-2 border-b">
    <span className="font-semibold text-sm text-muted-foreground">{label}</span>
    <span className="col-span-2 text-sm">{value || "N/A"}</span>
  </div>
);

export default function ViewUserDialog({
  userId,
  isOpen,
  onOpenChange,
}: ViewUserDialogProps) {
  const t = useTranslations("Admin.EmployeeManagement");
  const format = useFormatter();

  const {
    data: user,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: queryKeys.admin.userDetails.detail(userId!),
    queryFn: () => getAdminUserDetail(userId!),
    enabled: !!userId && isOpen, // Only fetch when the dialog is open with a valid user ID
  });

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="space-y-3 pt-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="grid grid-cols-3 gap-4">
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-5 w-48 col-span-2" />
            </div>
          ))}
        </div>
      );
    }

    if (isError) {
      return (
        <Alert variant="destructive" className="mt-4">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      );
    }

    if (user) {
      return (
        <div className="space-y-2 pt-4">
          <DetailRow label={t("table.name")} value={user.full_name} />
          <DetailRow label={t("table.email")} value={user.user.email} />
          <DetailRow label={t("table.role")} value={t(`roles.${user.role}`)} />
          <DetailRow
            label={t("table.status")}
            value={
              <Badge variant={user.user.is_active ? "default" : "secondary"}>
                {user.user.is_active
                  ? t("statuses.active")
                  : t("statuses.inactive")}
              </Badge>
            }
          />
          <DetailRow
            label={t("table.joinDate")}
            value={format.dateTime(new Date(user.user.date_joined), {
              dateStyle: "long",
            })}
          />
          <DetailRow label={t("points")} value={user.points} />
          <DetailRow
            label={t("subscribed")}
            value={user.is_subscribed ? t("yes") : t("no")}
          />
        </div>
      );
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t("viewDetails")}</DialogTitle>
          <DialogDescription>
            {user
              ? t("viewDetailsDescription", { fullName: user.full_name })
              : t("loadingUserDetails")}
          </DialogDescription>
        </DialogHeader>
        {renderContent()}
      </DialogContent>
    </Dialog>
  );
}
