import { StatisticsDashboard } from "@/components/features/platform/study/statistics/StatisticsDashboard";
import { getTranslations } from "next-intl/server";

export default async function StatisticsPage() {
  const t = await getTranslations("Study.statistics");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
        {t("pageTitle")}
      </h1>
      <p className="text-muted-foreground">{t("pageDescription")}</p>

      <StatisticsDashboard />
    </div>
  );
}
