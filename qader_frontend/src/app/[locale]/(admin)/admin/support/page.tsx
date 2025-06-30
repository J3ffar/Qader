import { useTranslations } from "next-intl";
import { SupportInboxLayout } from "@/components/features/admin/support/inbox/SupportInboxLayout";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function AdminSupportPage() {
  const t = useTranslations("Admin.support");

  return (
    <div className="h-full flex flex-col">
      <CardHeader className="flex-shrink-0">
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      {/* The layout component will manage its own padding and borders */}
      <SupportInboxLayout />
    </div>
  );
}
