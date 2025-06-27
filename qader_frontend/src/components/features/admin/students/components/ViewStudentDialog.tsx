import { useTranslations, useFormatter } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/constants/queryKeys";
import { getAdminUserDetail } from "@/services/api/admin/users.service";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { User } from "lucide-react";

interface ViewStudentDialogProps {
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
    <span className="font-semibold text-sm text-muted-foreground rtl:pl-2 ltr:pr-2">
      {label}
    </span>
    <span className="col-span-2 text-sm break-words">{value || "N/A"}</span>
  </div>
);

const ProfileHeader = ({
  name,
  email,
  avatarUrl,
}: {
  name: string;
  email: string;
  avatarUrl: string | null;
}) => (
  <div className="flex items-center gap-4">
    <Avatar className="h-16 w-16">
      <AvatarImage src={avatarUrl ?? undefined} alt={name} />
      <AvatarFallback>
        <User className="h-8 w-8" />
      </AvatarFallback>
    </Avatar>
    <div>
      <DialogTitle className="text-2xl">{name}</DialogTitle>
      <p className="text-muted-foreground">{email}</p>
    </div>
  </div>
);

export default function ViewStudentDialog({
  userId,
  isOpen,
  onOpenChange,
}: ViewStudentDialogProps) {
  const t = useTranslations("Admin.StudentManagement");
  const tCommon = useTranslations("Common");
  const format = useFormatter();

  const {
    data: user,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: queryKeys.admin.userDetails.detail(userId!),
    queryFn: () => getAdminUserDetail(userId!),
    enabled: !!userId && isOpen,
  });

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="space-y-2 pt-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      );
    }

    if (isError) {
      return (
        <Alert variant="destructive" className="mt-4">
          <AlertTitle>{tCommon("error")}</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      );
    }

    if (user) {
      return (
        <div className="space-y-1 pt-4">
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
            label={t("table.subscribed")}
            value={user.is_subscribed ? tCommon("yes") : tCommon("no")}
          />
          {user.subscription_expires_at && (
            <DetailRow
              label={t("subscriptionExpires")}
              value={format.dateTime(new Date(user.subscription_expires_at), {
                dateStyle: "long",
              })}
            />
          )}
          <DetailRow
            label={t("table.points")}
            value={<Badge variant="outline">{user.points}</Badge>}
          />
          <DetailRow label={t("grade")} value={user.grade} />
          <DetailRow
            label={t("levelVerbal")}
            value={user.current_level_verbal}
          />
          <DetailRow
            label={t("levelQuantitative")}
            value={user.current_level_quantitative}
          />
          <DetailRow
            label={t("table.joinDate")}
            value={format.dateTime(new Date(user.user.date_joined), {
              dateStyle: "long",
            })}
          />
          {user.user.last_login && (
            <DetailRow
              label={t("lastLogin")}
              value={format.dateTime(new Date(user.user.last_login), {
                dateStyle: "long",
                timeStyle: "short",
              })}
            />
          )}
        </div>
      );
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          {isLoading ? (
            <div className="flex items-center gap-4">
              <Skeleton className="h-16 w-16 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-6 w-40" />
                <Skeleton className="h-4 w-52" />
              </div>
            </div>
          ) : user ? (
            <ProfileHeader
              name={user.full_name}
              email={user.user.email}
              avatarUrl={user.profile_picture}
            />
          ) : (
            <DialogTitle>{t("viewDetails")}</DialogTitle>
          )}
        </DialogHeader>
        {renderContent()}
      </DialogContent>
    </Dialog>
  );
}
