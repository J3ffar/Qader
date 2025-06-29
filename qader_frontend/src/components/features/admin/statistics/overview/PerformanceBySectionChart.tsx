"use client";

import { useTranslations } from "next-intl";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";
import { PerformanceBySection } from "@/types/api/admin/statistics.types";

interface PerformanceBySectionChartProps {
  data: PerformanceBySection[];
}

export function PerformanceBySectionChart({
  data,
}: PerformanceBySectionChartProps) {
  const t = useTranslations("Admin.AdminStatistics");

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="section_name"
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `${value}%`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "var(--background)",
            borderColor: "var(--foreground)",
          }}
        />
        <Legend />
        <Bar
          dataKey="average_accuracy"
          name={t("accuracy")}
          fill="var(--primary)"
        />
        <Bar
          dataKey="total_attempts"
          name={t("attempts")}
          fill="var(--foreground)"
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
