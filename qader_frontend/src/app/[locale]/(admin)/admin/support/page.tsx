import { useTranslations } from "next-intl";
import { SupportClient } from "@/components/features/admin/support/SupportClient";
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
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <SupportClient />
      </CardContent>
    </Card>
  );
}
