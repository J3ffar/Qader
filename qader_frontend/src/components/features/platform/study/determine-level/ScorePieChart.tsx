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
  percentage?: number;
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
  let total = 0;

  // Calculate total first
  if (verbalScore !== null && verbalScore !== undefined) {
    total += verbalScore;
  }
  if (quantitativeScore !== null && quantitativeScore !== undefined) {
    total += quantitativeScore;
  }

  // Build data with percentages
  if (verbalScore !== null && verbalScore !== undefined) {
    data.push({
      name: t("verbalSection"),
      value: verbalScore,
      color: "#E6B11D",
      percentage: total > 0 ? (verbalScore / total) * 100 : 0,
    });
  }
  if (quantitativeScore !== null && quantitativeScore !== undefined) {
    data.push({
      name: t("quantitativeSection"),
      value: quantitativeScore,
      color: "#074182",
      percentage: total > 0 ? (quantitativeScore / total) * 100 : 0,
    });
  }

  // If no data, render nothing or a placeholder
  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        {t("noScoreDataForChart")}
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Score percentages displayed directly */}
      <div className="mb-4 flex justify-center gap-6 text-sm">
        {data.map((item, index) => (
          <div key={index} className="flex items-center gap-2">
            <div
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            <span className="font-medium">{item.name}:</span>
            <span className="font-bold">
              {item.value}%
            </span>
          </div>
        ))}
      </div>

      {/* Pie Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ value }) => `${value}%`}
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
    </div>
  );
};

export default ScorePieChart;
