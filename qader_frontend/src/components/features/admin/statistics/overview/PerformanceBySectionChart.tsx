"use client";

import { useTranslations } from "next-intl";
import {
  ComposedChart,
  Bar,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";
import { type PerformanceBySection } from "@/types/api/admin/statistics.types";

interface PerformanceBySectionChartProps {
  data: PerformanceBySection[];
}

export function PerformanceBySectionChart({
  data,
}: PerformanceBySectionChartProps) {
  const t = useTranslations("Admin.AdminStatistics");

  const formattedData = data.map((item) => ({
    ...item,
    average_accuracy: item.average_accuracy
      ? parseFloat(item.average_accuracy.toFixed(1))
      : 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <ComposedChart data={formattedData}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="section_name"
          stroke="var(--muted-foreground)"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          yAxisId="left"
          stroke="var(--muted-foreground)"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          label={{
            value: t("totalAttempts"),
            angle: -90,
            position: "insideLeft",
            style: {
              textAnchor: "middle",
              fill: "var(--muted-foreground)",
            },
          }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          stroke="var(--muted-foreground)"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          domain={[0, 100]}
          tickFormatter={(value) => `${value}%`}
          label={{
            value: t("avgAccuracy"),
            angle: 90,
            position: "insideRight",
            style: {
              textAnchor: "middle",
              fill: "var(--muted-foreground)",
            },
          }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "var(--background)",
            borderColor: "var(--border)",
            borderRadius: "var(--radius)",
          }}
          formatter={(value, name, props) => {
            if (props.dataKey === "average_accuracy") {
              return [`${value}%`, name];
            }
            return [value, name];
          }}
        />
        <Legend />
        <Bar
          yAxisId="left"
          dataKey="total_attempts"
          name={t("totalAttempts")}
          fill="var(--chart-1)"
          radius={[4, 4, 0, 0]}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="average_accuracy"
          name={t("avgAccuracy")}
          stroke="var(--chart-2)"
          strokeWidth={2}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
