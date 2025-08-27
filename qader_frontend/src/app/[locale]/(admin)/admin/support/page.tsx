import { useTranslations } from "next-intl";
import { SupportInboxLayout } from "@/components/features/admin/support/inbox/SupportInboxLayout";
import { CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function AdminSupportPage() {
  const t = useTranslations("Admin.support");

  return (
    // 1. h-full flex flex-col: This makes the page a full-height container.
    // The header will take its natural height, and SupportInboxLayout will fill the rest.
    <div className="h-full flex flex-col">
      <CardHeader className="flex-shrink-0 pb-5">
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <SupportInboxLayout />
    </div>
  );
}
