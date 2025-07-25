"use client";

import React, { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { queryKeys } from "@/constants/queryKeys";
import { getAdminQuestionDetail } from "@/services/api/admin/learning.service";
import { AdminQuestionUsageByTestType } from "@/types/api/admin/learning.types";
import { cn } from "@/lib/utils";
import { RichContentViewer } from "@/components/shared/RichContentViewer";
import {
  CheckCircle2,
  Hash,
  Tag,
  Activity,
  BrainCircuit,
  Lightbulb,
} from "lucide-react";

interface ViewQuestionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  questionId: number | null;
}

// --- Detail Components for Readability ---
const DetailRow = ({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: React.ReactNode;
}) => (
  <div className="flex items-start gap-3">
    <Icon className="h-5 w-5 text-muted-foreground mt-1 flex-shrink-0" />
    <div className="flex flex-col">
      <dt className="text-sm font-semibold text-muted-foreground">{label}</dt>
      <dd className="text-sm text-foreground">{value ?? "غير متوفر"}</dd>
    </div>
  </div>
);

// --- Mappings for clean display ---
const arabicOptionMap: { [key: string]: string } = {
  A: "أ",
  B: "ب",
  C: "ج",
  D: "د",
};

const difficultyMap: { [key: number]: { label: string; className: string } } = {
  1: {
    label: "سهل جداً",
    className:
      "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300",
  },
  2: {
    label: "سهل",
    className:
      "bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300",
  },
  3: {
    label: "متوسط",
    className:
      "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300",
  },
  4: {
    label: "صعب",
    className:
      "bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-300",
  },
  5: {
    label: "صعب جداً",
    className: "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300",
  },
};

const usageMap: { [key in keyof AdminQuestionUsageByTestType]: string } = {
  level_assessment: "تقييم المستوى",
  practice: "اختبارات",
  simulation: "اختبار محاكاة",
  traditional: "تعلم تقليدي",
};

function ViewSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4">
      {/* Main Content Skeleton */}
      <div className="lg:col-span-2 space-y-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-1/3" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-24 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-1/4" />
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </CardContent>
        </Card>
      </div>
      {/* Sidebar Skeleton */}
      <div className="lg:col-span-1 space-y-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-1/2" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function ViewQuestionDialog({
  isOpen,
  onClose,
  questionId,
}: ViewQuestionDialogProps) {
  const { data: question, isLoading } = useQuery({
    queryKey: queryKeys.admin.learning.questions.detail(questionId!),
    queryFn: () => getAdminQuestionDetail(questionId!),
    enabled: isOpen && questionId !== null,
  });

  const renderContent = () => {
    if (isLoading) {
      return <ViewSkeleton />;
    }
    if (!question) {
      return <div className="text-center py-8">بيانات السؤال غير موجودة.</div>;
    }

    const difficultyInfo = difficultyMap[question.difficulty] || {
      label: "N/A",
      className: "",
    };

    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4">
        {/* Main Content Column */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>نص السؤال</CardTitle>
            </CardHeader>
            <CardContent>
              <RichContentViewer htmlContent={question.question_text} />
              {question.image && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-muted-foreground mb-2">
                    الصورة المرفقة
                  </p>
                  <img
                    src={question.image}
                    alt="صورة السؤال"
                    className="max-w-md w-full rounded-md border"
                  />
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>الخيارات</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(question.options).map(([key, value]) => {
                const isCorrect = question.correct_answer === key;
                return (
                  <div
                    key={key}
                    className={cn(
                      "p-4 rounded-lg border flex items-start gap-3 transition-all",
                      isCorrect
                        ? "bg-green-50 border-green-500 dark:bg-green-900/30"
                        : "bg-muted/50"
                    )}
                  >
                    {isCorrect && (
                      <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                    )}
                    <div className="flex flex-col w-full">
                      <span className="font-bold text-sm text-muted-foreground">
                        الخيار {arabicOptionMap[key] || key}
                      </span>
                      <RichContentViewer htmlContent={value} />
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {(question.explanation ||
            question.hint ||
            question.solution_method_summary) && (
            <Card>
              <CardHeader>
                <CardTitle>معلومات مساعدة</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {question.explanation && (
                  <DetailRow
                    icon={Lightbulb}
                    label="الشرح"
                    value={
                      <RichContentViewer htmlContent={question.explanation} />
                    }
                  />
                )}
                {question.hint && (
                  <DetailRow
                    icon={Lightbulb}
                    label="تلميح"
                    value={<RichContentViewer htmlContent={question.hint} />}
                  />
                )}
                {question.solution_method_summary && (
                  <DetailRow
                    icon={Lightbulb}
                    label="ملخص الحل"
                    value={
                      <RichContentViewer
                        htmlContent={question.solution_method_summary}
                      />
                    }
                  />
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar Column */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>تفاصيل السؤال</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <DetailRow icon={Hash} label="المعرف" value={question.id} />
              <DetailRow
                icon={Activity}
                label="الحالة"
                value={
                  <Badge
                    variant={question.is_active ? "default" : "outline"}
                    className={question.is_active ? "bg-primary" : ""}
                  >
                    {question.is_active ? "نشط" : "غير نشط"}
                  </Badge>
                }
              />
              <DetailRow
                icon={Tag}
                label="مستوى الصعوبة"
                value={
                  <Badge
                    className={cn("font-semibold", difficultyInfo.className)}
                  >
                    {difficultyInfo.label}
                  </Badge>
                }
              />
              <Separator />
              <DetailRow
                icon={BrainCircuit}
                label="التسلسل الهرمي"
                value={
                  <div className="flex flex-col text-sm">
                    <span>{question.section.name}</span>
                    <span className="rtl:pr-2 ltr:pl-2">
                      {" > "}
                      {question.subsection.name}
                    </span>
                    {question.skill && (
                      <span className="rtl:pr-4 ltr:pl-4">
                        {" >> "}
                        {question.skill.name}
                      </span>
                    )}
                  </div>
                }
              />
            </CardContent>
          </Card>

          {question.usage_by_test_type && (
            <Card>
              <CardHeader>
                <CardTitle>إحصائيات الاستخدام</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-semibold text-muted-foreground">
                    إجمالي الاستخدام
                  </span>
                  <Badge variant="secondary" className="text-base">
                    {question.total_usage_count}
                  </Badge>
                </div>
                <Separator />
                {Object.entries(question.usage_by_test_type).map(
                  ([key, value]) => (
                    <div
                      key={key}
                      className="flex justify-between items-center text-sm"
                    >
                      <span className="text-muted-foreground">
                        {usageMap[key as keyof typeof usageMap] || key}
                      </span>
                      <span className="font-mono font-semibold">{value}</span>
                    </div>
                  )
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="md:max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>تفاصيل السؤال</DialogTitle>
          <DialogDescription>
            عرض للقراءة فقط لبيانات السؤال وإحصائياته.
          </DialogDescription>
        </DialogHeader>
        {renderContent()}
      </DialogContent>
    </Dialog>
  );
}
