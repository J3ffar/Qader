"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { UserStatistics } from "@/types/api/study.types";

interface Props {
  trends: UserStatistics["performance_trends_by_test_type"];
}

// Flatten and merge data for the chart
const processChartData = (trends: Props["trends"]) => {
  const dataMap = new Map<string, any>();

  Object.values(trends).forEach((trendArray) => {
    trendArray.forEach((point) => {
      const date = point.period_start_date
        ? new Date(point.period_start_date).toLocaleDateString()
        : new Date(point.date!).toLocaleDateString();
      if (!dataMap.has(date)) {
        dataMap.set(date, { date });
      }
      const entry = dataMap.get(date);
      entry.overallScore = point.average_score ?? point.score;
      entry.verbalScore = point.average_verbal_score ?? point.verbal_score;
      entry.quantScore =
        point.average_quantitative_score ?? point.quantitative_score;
    });
  });

  return Array.from(dataMap.values()).sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );
};

export function PerformanceTrendsChart({ trends }: Props) {
  const t = useTranslations("Study.statistics.charts");
  const chartData = processChartData(trends);

  return (
    <Card className="col-span-1 lg:col-span-3">
      <CardHeader>
        <CardTitle>{t("performanceTrendTitle")}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="overallScore"
              name={t("overallScore")}
              stroke="hsl(var(--primary))"
            />
            <Line
              type="monotone"
              dataKey="verbalScore"
              name={t("verbalScore")}
              stroke="hsl(var(--chart-2))"
            />
            <Line
              type="monotone"
              dataKey="quantScore"
              name={t("quantScore")}
              stroke="hsl(var(--chart-3))"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
