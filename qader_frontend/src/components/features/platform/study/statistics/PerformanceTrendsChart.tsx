"use client";

import React, { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { BarChart3, LineChart as LineChartIcon } from "lucide-react";
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
import type { TooltipProps } from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import {
  NameType,
  ValueType,
} from "recharts/types/component/DefaultTooltipContent";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import type { UserStatistics } from "@/types/api/study.types";

interface Props {
  trends: UserStatistics["performance_trends_by_test_type"];
  isLoading?: boolean;
}

const TEST_TYPE_COLORS: Record<string, string> = {
  level_assessment: "#8b5cf6", // Vibrant Purple
  practice: "#06b6d4", // Bright Cyan
  simulation: "#f59e0b", // Warm Amber
  traditional: "#ec4899", // Energetic Pink
  default: "#64748b", // Neutral Slate
};

// Clean data processing function
const processChartData = (trends: Props["trends"], filter: string) => {
  const dataMap = new Map<string, any>();
  const testTypesToProcess = filter === "all" ? Object.keys(trends) : [filter];

  testTypesToProcess.forEach((testType) => {
    if (!trends[testType]) return;

    trends[testType].forEach((point) => {
      const dateString = point.period_start_date || point.date;
      if (!dateString) return;

      const date = new Date(dateString).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });

      if (!dataMap.has(date)) {
        dataMap.set(date, { date });
      }

      const entry = dataMap.get(date);
      const scoreValue = point.average_score ?? point.score;

      if (scoreValue != null && typeof scoreValue === "number") {
        entry[testType] = scoreValue;
      }
    });
  });

  return Array.from(dataMap.values()).sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );
};

const ChartPlaceholder = ({
  type,
  message,
  description,
}: {
  type: "loading" | "empty";
  message: string;
  description: string;
}) => (
  <div className="flex h-[400px] flex-col items-center justify-center space-y-4 p-8 text-center">
    {type === "loading" ? (
      <>
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-[250px]" />
          <Skeleton className="h-4 w-[200px]" />
        </div>
      </>
    ) : (
      <>
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
          <BarChart3 className="h-8 w-8 text-muted-foreground" />
        </div>
        <div className="space-y-1">
          <p className="text-lg font-semibold text-foreground">{message}</p>
          <p className="max-w-sm text-sm text-muted-foreground">
            {description}
          </p>
        </div>
      </>
    )}
  </div>
);

const CustomTooltip = ({
  active,
  payload,
  label,
}: TooltipProps<ValueType, NameType>) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border bg-card/80 p-3 shadow-lg ring-1 ring-black/5 backdrop-blur-sm">
        <p className="mb-2 border-b pb-2 text-sm font-bold text-card-foreground">
          {label}
        </p>
        <div className="space-y-2">
          {payload.map((p, i) =>
            p.value != null ? (
              <div
                className="flex items-center justify-between gap-4"
                key={`item-${i}`}
              >
                <div className="flex items-center gap-2.5">
                  <div
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ backgroundColor: p.color }}
                  />
                  <p className="text-sm font-medium text-muted-foreground">
                    {p.name}
                  </p>
                </div>
                <p className="text-sm font-semibold text-card-foreground">
                  {typeof p.value === "number" ? p.value.toFixed(1) : p.value}%
                </p>
              </div>
            ) : null
          )}
        </div>
      </div>
    );
  }
  return null;
};

const PerformanceIndicator = ({
  value,
  label,
}: {
  value: number;
  label: string;
}) => (
  <div className="flex flex-col items-center gap-1">
    <div className="text-2xl font-bold tracking-tighter text-foreground sm:text-3xl">
      {value.toFixed(1)}%
    </div>
    <div className="text-xs font-medium text-muted-foreground">{label}</div>
  </div>
);

export function PerformanceTrendsChart({ trends, isLoading = false }: Props) {
  const t = useTranslations("Study.statistics");
  const tCommon = useTranslations("Common");

  const availableTestTypes = useMemo(() => Object.keys(trends || {}), [trends]);
  const [selectedTestType, setSelectedTestType] = useState("all");

  const chartData = useMemo(
    () => processChartData(trends || {}, selectedTestType),
    [trends, selectedTestType]
  );

  const linesToRender =
    selectedTestType === "all" ? availableTestTypes : [selectedTestType];

  // ✨ NEW: Improved and more accurate summary statistics logic
  const summaryStats = useMemo(() => {
    if (!chartData || chartData.length === 0) return null;

    const allScores: number[] = chartData.flatMap((entry) =>
      linesToRender.map((type) => entry[type]).filter((v) => v != null)
    );

    if (allScores.length === 0) return null;

    const avg =
      allScores.reduce((sum, score) => sum + score, 0) / allScores.length;
    const max = Math.max(...allScores);

    const latestEntry = chartData[chartData.length - 1];
    const latestScores = linesToRender
      .map((type) => latestEntry[type])
      .filter((v): v is number => v != null);

    // UX Fix: Averages the latest scores if multiple are present, instead of showing just one
    const latestAvg =
      latestScores.length > 0
        ? latestScores.reduce((s, v) => s + v, 0) / latestScores.length
        : 0;

    return { avg, max, latest: latestAvg };
  }, [chartData, linesToRender]);

  const hasData = !isLoading && chartData.length > 0;

  return (
    <Card className="shadow-sm transition-shadow duration-300 hover:shadow-md">
      <CardHeader className="border-b">
        <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1.5">
            <CardTitle className="flex items-center gap-2 text-xl font-semibold">
              <LineChartIcon className="h-5 w-5 text-primary" />
              {t("charts.performanceTrendTitle")}
            </CardTitle>
            <CardDescription>{t("pageDescription")}</CardDescription>
          </div>
          <Select
            value={selectedTestType}
            onValueChange={setSelectedTestType}
            disabled={isLoading}
          >
            <SelectTrigger className="w-full min-w-[180px] sm:w-auto">
              <SelectValue placeholder={t("charts.filterPlaceholder")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("charts.allTestTypes")}</SelectItem>
              {availableTestTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  <div className="flex items-center gap-2">
                    <div
                      className="h-2 w-2 rounded-full"
                      style={{
                        backgroundColor:
                          TEST_TYPE_COLORS[type] || TEST_TYPE_COLORS.default,
                      }}
                    />
                    {tCommon(`testTypes.${type}`)}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <AnimatePresence>
          {summaryStats && hasData && (
            <motion.div
              initial={{ height: 0, opacity: 0, marginTop: 0 }}
              animate={{ height: "auto", opacity: 1, marginTop: "1rem" }}
              exit={{ height: 0, opacity: 0, marginTop: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="overflow-hidden"
            >
              <div className="flex items-center justify-around rounded-lg bg-muted/50 p-4">
                <PerformanceIndicator
                  value={summaryStats.avg}
                  label={t("charts.summary.average")}
                />
                <PerformanceIndicator
                  value={summaryStats.max}
                  label={t("charts.summary.peakScore")}
                />
                <PerformanceIndicator
                  value={summaryStats.latest}
                  label={t("charts.summary.latestScore")}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardHeader>

      <CardContent className="p-2 pt-6 sm:p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={isLoading ? "loading" : hasData ? "data" : "empty"}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {!hasData ? (
              <ChartPlaceholder
                type={isLoading ? "loading" : "empty"}
                message={
                  isLoading ? t("charts.loading") : t("charts.notEnoughData")
                }
                description={
                  isLoading
                    ? t("charts.loadingDescription")
                    : t("charts.notEnoughDataDescription")
                }
              />
            ) : (
              <ResponsiveContainer width="100%" height={350}>
                <LineChart
                  data={chartData}
                  margin={{ top: 5, right: 20, left: -10, bottom: 5 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="hsl(var(--border))"
                  />
                  <XAxis
                    dataKey="date"
                    tickLine={false}
                    axisLine={false}
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                    tickMargin={10}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                    tickMargin={10}
                    tickFormatter={(value) => `${value}%`}
                    domain={[0, 100]}
                  />
                  <Tooltip
                    content={<CustomTooltip />}
                    cursor={{
                      stroke: "hsl(var(--primary))",
                      strokeWidth: 1.5,
                      strokeDasharray: "4 4",
                    }}
                  />
                  <Legend
                    iconType="circle"
                    formatter={(value) => (
                      <span className="text-muted-foreground">{value}</span>
                    )}
                  />

                  {linesToRender.map((type) => (
                    <Line
                      key={type}
                      type="monotone"
                      dataKey={type}
                      name={tCommon(`testTypes.${type}`)}
                      stroke={
                        TEST_TYPE_COLORS[type] || TEST_TYPE_COLORS.default
                      }
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{
                        r: 6,
                        strokeWidth: 2,
                        fill: "hsl(var(--background))",
                      }}
                      // ✨ NEW: Animate line drawing on load
                      isAnimationActive={true}
                      animationDuration={700}
                      connectNulls={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </motion.div>
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
