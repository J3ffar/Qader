// This is the refactored content of the old ViewStudentDialog
import { useFormatter, useTranslations } from "next-intl";
import { AdminUserProfile } from "@/types/api/admin/users.types";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

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

interface ProfileDetailsTabProps {
  user: AdminUserProfile | undefined;
  isLoading: boolean;
}

export function ProfileDetailsTab({ user, isLoading }: ProfileDetailsTabProps) {
  const t = useTranslations("Admin.StudentManagement");
  const tCommon = useTranslations("Common");
  const format = useFormatter();

  if (isLoading) {
    return (
      <div className="space-y-2 pt-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-8 w-full" />
        ))}
      </div>
    );
  }

  if (!user) {
    return (
      <div className="text-center text-muted-foreground">
        {tCommon("noData")}
      </div>
    );
  }

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
      <DetailRow label={t("points")} value={user.points} />
      <DetailRow
        label={t("subscribed")}
        value={user.is_subscribed ? tCommon("yes") : tCommon("no")}
      />
      {user.is_subscribed && user.subscription_expires_at && (
        <DetailRow
          label={t("subscriptionExpires")}
          value={format.dateTime(new Date(user.subscription_expires_at), {
            dateStyle: "long",
          })}
        />
      )}
      <DetailRow label={t("grade")} value={user.grade} />
      <DetailRow
        label={t("levelDetermined")}
        value={user.level_determined ? tCommon("yes") : tCommon("no")}
      />
      <DetailRow label={t("verbalLevel")} value={user.current_level_verbal} />
      <DetailRow
        label={t("quantitativeLevel")}
        value={user.current_level_quantitative}
      />
      <DetailRow
        label={t("language")}
        value={user.language === "ar" ? "العربية" : "English"}
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
