"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { DateRange } from "react-day-picker";
import { format } from "date-fns";
import { toast } from "sonner";
import {
  Users,
  HelpCircle,
  CheckCircle,
  ClipboardList,
  Target,
  Percent,
  Calendar as CalendarIcon,
  Download,
} from "lucide-react";

import { queryKeys } from "@/constants/queryKeys";
import {
  getStatisticsOverview,
  exportStatistics,
} from "@/services/api/admin/statistics.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";

import StatisticsOverviewSkeleton from "./StatisticsOverviewSkeleton";
import { StatCard } from "./StatCard";
import { DailyActivityChart } from "./DailyActivityChart";
import { PerformanceBySectionChart } from "./PerformanceBySectionChart";
import { QuestionDataTable } from "./QuestionDataTable";

const StatCards = ({ data }: { data: any }) => {
  const t = useTranslations("Admin.AdminStatistics");
  const cards = [
    {
      title: t("totalActiveStudents"),
      value: data.total_active_students,
      icon: Users,
    },
    {
      title: t("newRegistrations"),
      value: data.new_registrations_period,
      icon: Users,
    },
    {
      title: t("questionsAnswered"),
      value: data.total_questions_answered_period,
      icon: HelpCircle,
    },
    {
      title: t("testsCompleted"),
      value: data.total_tests_completed_period,
      icon: CheckCircle,
    },
    {
      title: t("avgTestScore"),
      value: `${data.overall_average_test_score?.toFixed(1) ?? "N/A"}%`,
      icon: Target,
    },
    {
      title: t("avgAccuracy"),
      value: `${data.overall_average_accuracy?.toFixed(1) ?? "N/A"}%`,
      icon: Percent,
    },
  ];
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {cards.map((card) => (
        <StatCard key={card.title} {...card} />
      ))}
    </div>
  );
};

// Main Client Component
export function StatisticsOverviewClient() {
  const t = useTranslations("Admin.AdminStatistics");
  const queryClient = useQueryClient();

  const defaultDateRange = {
    from: new Date(new Date().setDate(new Date().getDate() - 30)),
    to: new Date(),
  };

  const [date, setDate] = useState<DateRange | undefined>(defaultDateRange);

  const filters = {
    date_from: date?.from ? format(date.from, "yyyy-MM-dd") : undefined,
    date_to: date?.to ? format(date.to, "yyyy-MM-dd") : undefined,
  };

  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.admin.statistics.overview(filters),
    queryFn: () => getStatisticsOverview(filters),
  });

  const { mutate: handleExport, isPending: isExporting } = useMutation({
    mutationFn: () => exportStatistics({ ...filters, format: "xlsx" }),
    onSuccess: (data) => {
      toast.success(data.message || t("exportSuccess"));
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, "قد حدث خطأ ما"));
    },
  });

  if (isLoading) {
    return <StatisticsOverviewSkeleton />;
  }

  if (isError) {
    return (
      <div className="text-center py-10 text-destructive">
        Error loading statistics: {getApiErrorMessage(error, "قد حدث خطأ ما")}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-2 md:space-y-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{t("title")}</h2>
          <p className="text-muted-foreground">{t("subtitle")}</p>
        </div>
        <div className="flex items-center space-x-2 rtl:space-x-reverse">
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant={"outline"}
                className="w-[280px] justify-start text-left font-normal"
              >
                <CalendarIcon className="me-2 h-4 w-4" />
                {date?.from ? (
                  date.to ? (
                    <>
                      {format(date.from, "LLL dd, y")} -{" "}
                      {format(date.to, "LLL dd, y")}
                    </>
                  ) : (
                    format(date.from, "LLL dd, y")
                  )
                ) : (
                  <span>{t("pickDateRange")}</span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="end">
              <Calendar
                initialFocus
                mode="range"
                defaultMonth={date?.from}
                selected={date}
                onSelect={setDate}
                numberOfMonths={2}
              />
            </PopoverContent>
          </Popover>
          <Button onClick={() => handleExport()} disabled={isExporting}>
            <Download className="me-2 h-4 w-4" />
            {isExporting ? t("exporting") : t("exportData")}
          </Button>
        </div>
      </div>

      <StatCards data={data} />

      <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t("dailyActivity")}</CardTitle>
          </CardHeader>
          <CardContent className="pl-2 rtl:pl-0 rtl:pr-2">
            <DailyActivityChart data={data.daily_activity} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{t("performanceBySection")}</CardTitle>
          </CardHeader>
          <CardContent>
            <PerformanceBySectionChart data={data.performance_by_section} />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QuestionDataTable
          title={t("mostAttemptedQuestions")}
          data={data.most_attempted_questions}
        />
        <QuestionDataTable
          title={t("lowestAccuracyQuestions")}
          data={data.lowest_accuracy_questions}
        />
      </div>
    </div>
  );
}
