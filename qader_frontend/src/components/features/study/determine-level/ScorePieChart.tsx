"use client";

import React from "react";
import { useTranslations } from "next-intl";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

interface ScoreDataPoint {
  name: string;
  value: number;
  color: string;
}

interface ScorePieChartProps {
  verbalScore?: number | null;
  quantitativeScore?: number | null;
}

const ScorePieChart: React.FC<ScorePieChartProps> = ({
  verbalScore,
  quantitativeScore,
}) => {
  const t = useTranslations("Study.determineLevel.score");

  const data: ScoreDataPoint[] = [];
  if (verbalScore !== null && verbalScore !== undefined) {
    data.push({
      name: t("verbalSection"),
      value: verbalScore,
      color: "#E6B11D",
    }); // Yellowish for Verbal
  }
  if (quantitativeScore !== null && quantitativeScore !== undefined) {
    data.push({
      name: t("quantitativeSection"),
      value: quantitativeScore,
      color: "#074182",
    }); // Blue for Quantitative
  }

  // If no data, render nothing or a placeholder
  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        {t("noScoreDataForChart")}
      </div>
    );
  }
  // If only one score is available, pie chart might not be ideal, but Recharts handles it.
  // Or, display it differently. For now, let Recharts handle it.

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) =>
            `${name}: ${(percent * 100).toFixed(0)}%`
          }
          outerRadius={80}
          innerRadius={50} // For a donut chart effect
          fill="#8884d8"
          dataKey="value"
          stroke="hsl(var(--background))" // Add a stroke matching background for better separation
          strokeWidth={2}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number, name: string) => [`${value}%`, name]}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default ScorePieChart;
