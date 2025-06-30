// qader_frontend/src/app/[locale]/(admin)/admin/statistics/overview/page.tsx
import { getTranslations } from "next-intl/server";
import { StatisticsOverviewClient } from "@/components/features/admin/statistics/overview/StatisticsOverviewClient";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>; // FIX
}) {
  const { locale } = await params;
  const t = await getTranslations({
    locale,
    namespace: "Admin.AdminStatistics",
  });
  return {
    title: t("title"),
  };
}

export default function StatisticsOverviewPage() {
  return <StatisticsOverviewClient />;
}
