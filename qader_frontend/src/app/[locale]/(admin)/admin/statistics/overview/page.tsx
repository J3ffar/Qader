import { getTranslations } from "next-intl/server";
import { StatisticsOverviewClient } from "@/components/features/admin/statistics/overview/StatisticsOverviewClient";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
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
