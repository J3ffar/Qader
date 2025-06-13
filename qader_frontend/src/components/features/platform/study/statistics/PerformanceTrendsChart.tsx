"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
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

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { UserStatistics } from "@/types/api/study.types";

interface Props {
  trends: UserStatistics["performance_trends_by_test_type"];
}

const processChartData = (
  trends: Props["trends"],
  filter: string,
  t: (key: string) => string
) => {
  const dataMap = new Map<string, any>();
  const testTypesToProcess = filter === "all" ? Object.keys(trends) : [filter];

  testTypesToProcess.forEach((testType) => {
    if (!trends[testType]) return;
    trends[testType].forEach((point) => {
      const date = new Date(
        point.period_start_date || point.date!
      ).toLocaleDateString();
      if (!dataMap.has(date)) {
        dataMap.set(date, { date });
      }
      const entry = dataMap.get(date);
      const testTypeName = t(`testTypes.${testType}`) || testType;

      // Use a dynamic key for the score to avoid overwriting data from different test types
      entry[testTypeName] = point.average_score ?? point.score;
    });
  });

  return Array.from(dataMap.values()).sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );
};

export function PerformanceTrendsChart({ trends }: Props) {
  const t = useTranslations("Study.statistics.charts");
  const tCommon = useTranslations("Common");

  const availableTestTypes = Object.keys(trends);
  const [selectedTestType, setSelectedTestType] = useState("all");

  const chartData = useMemo(
    () => processChartData(trends, selectedTestType, tCommon),
    [trends, selectedTestType, tCommon]
  );

  const linesToRender =
    selectedTestType === "all" ? availableTestTypes : [selectedTestType];

  const lineColors = [
    "text-primary",
    "text-chart-2",
    "text-chart-3",
    "text-chart-4",
  ];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{t("performanceTrendTitle")}</CardTitle>
        <Select value={selectedTestType} onValueChange={setSelectedTestType}>
          <SelectTrigger className="w-auto min-w-[180px] gap-2">
            <SelectValue placeholder={t("filterPlaceholder")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("allTestTypes")}</SelectItem>
            {availableTestTypes.map((type) => (
              <SelectItem key={type} value={type}>
                {tCommon(`testTypes.${type}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="date"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              stroke="hsl(var(--muted-foreground))"
            />
            <YAxis
              fontSize={12}
              tickLine={false}
              axisLine={false}
              stroke="hsl(var(--muted-foreground))"
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--popover))",
                color: "hsl(var(--popover-foreground))",
                borderColor: "hsl(var(--border))",
                borderRadius: "var(--radius-md)",
              }}
            />
            <Legend
              formatter={(value, entry, index) => (
                <span className="text-muted-foreground">{value}</span>
              )}
            />
            {linesToRender.map((type, index) => (
              <Line
                key={type}
                type="monotone"
                dataKey={tCommon(`testTypes.${type}`)}
                // Use Tailwind classes and currentColor for theme-aware styling
                className={lineColors[index % lineColors.length]}
                stroke="currentColor"
                strokeWidth={2}
                dot={{
                  stroke: "currentColor",
                  strokeWidth: 2,
                  r: 4,
                  fill: "hsl(var(--background))",
                }}
                activeDot={{
                  stroke: "currentColor",
                  strokeWidth: 2,
                  r: 6,
                  fill: "hsl(var(--background))",
                }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
