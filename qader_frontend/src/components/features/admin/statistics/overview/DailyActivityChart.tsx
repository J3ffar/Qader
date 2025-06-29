"use client";

import { useTranslations } from "next-intl";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";
import { type DailyActivity } from "@/types/api/admin/statistics.types";

interface DailyActivityChartProps {
  data: DailyActivity[];
}

export function DailyActivityChart({ data }: DailyActivityChartProps) {
  const t = useTranslations("Admin.AdminStatistics");

  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
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
          tickFormatter={(value) => `${value}`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "var(--background)",
            borderColor: "var(--foreground)",
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="questions_answered"
          name={t("questions")}
          stroke="var(--primary)"
          activeDot={{ r: 8 }}
        />
        <Line
          type="monotone"
          dataKey="tests_completed"
          name={t("tests")}
          stroke="var(--foreground)"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
