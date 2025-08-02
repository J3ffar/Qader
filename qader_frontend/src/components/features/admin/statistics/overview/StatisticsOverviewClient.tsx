"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { DateRange } from "react-day-picker";
import { format } from "date-fns";
import { toast } from "sonner";
import {
  Users,
  UserPlus,
  HelpCircle,
  ClipboardCheck,
  Target,
  Percent,
  Calendar as CalendarIcon,
  Download,
  List, // New Icon
} from "lucide-react";

import { queryKeys } from "@/constants/queryKeys";
import {
  getStatisticsOverview,
  createExportJob, // Updated service function
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import StatisticsOverviewSkeleton from "./StatisticsOverviewSkeleton";
import { StatCard } from "./StatCard";
import { DailyActivityChart } from "./DailyActivityChart";
import { PerformanceBySectionChart } from "./PerformanceBySectionChart";
import { QuestionStatsTable } from "./QuestionStatsTable";
import { ExportJobsDialog } from "./ExportJobsDialog"; // Import the new dialog

const StatCards = ({ data }: { data: any }) => {
  // Use hardcoded Arabic text as requested
  // const t = useTranslations("Admin.AdminStatistics");
  const cards = [
    {
      title: "إجمالي الطلاب النشطين",
      value: data.total_active_students,
      icon: Users,
      description: "إجمالي الطلاب على المنصة",
    },
    {
      title: "التسجيلات الجديدة",
      value: `+${data.new_registrations_period}`,
      icon: UserPlus,
      description: "في الفترة المحددة",
    },
    {
      title: "الأسئلة التي تم الإجابة عليها",
      value: data.total_questions_answered_period.toLocaleString(),
      icon: HelpCircle,
      description: "في الفترة المحددة",
    },
    {
      title: "الاختبارات المكتملة",
      value: data.total_tests_completed_period.toLocaleString(),
      icon: ClipboardCheck,
      description: "في الفترة المحددة",
    },
    {
      title: "متوسط درجة الاختبار",
      value: `${data.overall_average_test_score?.toFixed(1) ?? "N/A"}%`,
      icon: Target,
      description: "المعدل العام",
    },
    {
      title: "متوسط الدقة",
      value: `${data.overall_average_accuracy?.toFixed(1) ?? "N/A"}%`,
      icon: Percent,
      description: "عبر جميع الأسئلة",
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
  // Use hardcoded Arabic text as requested
  // const t = useTranslations("Admin.AdminStatistics");
  // const tCore = useTranslations("Core");
  const defaultDateRange = {
    from: new Date(new Date().setDate(new Date().getDate() - 30)),
    to: new Date(),
  };

  const [date, setDate] = useState<DateRange | undefined>(defaultDateRange);
  const [isJobsDialogOpen, setIsJobsDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const filters = {
    date_from: date?.from ? format(date.from, "yyyy-MM-dd") : undefined,
    date_to: date?.to ? format(date.to, "yyyy-MM-dd") : undefined,
  };

  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.admin.statistics.overview(filters),
    queryFn: () => getStatisticsOverview(filters),
    placeholderData: (previousData) => previousData,
  });

  const { mutate: handleExport, isPending: isExporting } = useMutation({
    mutationFn: () => createExportJob({ ...filters, format: "xlsx" }),
    onSuccess: (data) => {
      toast.success("تم استلام طلب التصدير الخاص بك وهو قيد المعالجة.");
      // Invalidate query to refetch the list in the dialog
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.exportJobs.all,
      });
      // Open the dialog to show the user the new pending job
      setIsJobsDialogOpen(true);
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, "حدث خطأ غير متوقع."));
    },
  });

  if (isLoading && !data) {
    return <StatisticsOverviewSkeleton />;
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center text-destructive">
          <h3 className="text-lg font-semibold">{"حدث خطأ"}</h3>
          <p className="text-sm">
            {getApiErrorMessage(error, "فشل تحميل بيانات الإحصائيات.")}
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">
              {"لوحة تحكم الإحصائيات"}
            </h2>
            <p className="text-muted-foreground">
              {"نظرة عامة على أداء المنصة."}
            </p>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant={"outline"}
                  className="w-full sm:w-[280px] justify-start text-left font-normal"
                >
                  <CalendarIcon className="me-2 h-4 w-4" />
                  {date?.from ? (
                    date.to ? (
                      <>
                        {format(date.from, "d MMM, yyyy")} -{" "}
                        {format(date.to, "d MMM, yyyy")}
                      </>
                    ) : (
                      format(date.from, "d MMM, yyyy")
                    )
                  ) : (
                    <span>{"اختر نطاقًا زمنيًا"}</span>
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
            <Button
              variant="outline"
              onClick={() => setIsJobsDialogOpen(true)}
              className="w-full sm:w-auto"
            >
              <List className="me-2 h-4 w-4" />
              سجل التصدير
            </Button>
            <Button
              onClick={() => handleExport()}
              disabled={isExporting}
              className="w-full sm:w-auto"
            >
              <Download className="me-2 h-4 w-4" />
              {isExporting ? "جاري التصدير..." : "تصدير البيانات"}
            </Button>
          </div>
        </div>

        {data && <StatCards data={data} />}

        <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>النشاط اليومي</CardTitle>
            </CardHeader>
            <CardContent className="pl-2 rtl:pl-0 rtl:pr-2">
              {data && <DailyActivityChart data={data.daily_activity} />}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>الأداء حسب القسم</CardTitle>
            </CardHeader>
            <CardContent>
              {data && (
                <PerformanceBySectionChart data={data.performance_by_section} />
              )}
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="most-attempted">
          <TabsList className="grid w-full grid-cols-2 md:w-[400px]">
            <TabsTrigger value="most-attempted">
              الأسئلة الأكثر محاولة
            </TabsTrigger>
            <TabsTrigger value="lowest-accuracy">الأسئلة الأقل دقة</TabsTrigger>
          </TabsList>
          <TabsContent value="most-attempted">
            {data && (
              <QuestionStatsTable
                title="الأسئلة الأكثر محاولة"
                data={data.most_attempted_questions}
              />
            )}
          </TabsContent>
          <TabsContent value="lowest-accuracy">
            {data && (
              <QuestionStatsTable
                title="الأسئلة الأقل دقة"
                data={data.lowest_accuracy_questions}
              />
            )}
          </TabsContent>
        </Tabs>
      </div>

      <ExportJobsDialog
        isOpen={isJobsDialogOpen}
        onOpenChange={setIsJobsDialogOpen}
      />
    </>
  );
}
