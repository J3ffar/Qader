import { getTranslations } from "next-intl/server";
import { StatisticsOverviewClient } from "@/components/features/admin/statistics/overview/StatisticsOverviewClient";

export async function generateMetadata({
  params: { locale },
}: {
  params: { locale: string };
}) {
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
