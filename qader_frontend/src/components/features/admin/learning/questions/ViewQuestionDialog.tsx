"use client";

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
import { queryKeys } from "@/constants/queryKeys";
import { getAdminQuestionDetail } from "@/services/api/admin/learning.service";

interface ViewQuestionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  questionId: number | null;
}

const DetailRow = ({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) => (
  <div className="grid grid-cols-3 gap-4 py-2">
    <dt className="text-sm font-medium text-muted-foreground">{label}</dt>
    <dd className="text-sm col-span-2">{value ?? "غير متوفر"}</dd>
  </div>
);

const difficultyMap: { [key: number]: string } = {
  1: "1 - سهل جداً",
  2: "2 - سهل",
  3: "3 - متوسط",
  4: "4 - صعب",
  5: "5 - صعب جداً",
};

// NEW: A skeleton that better reflects the improved layout.
function ViewSkeleton() {
  return (
    <div className="space-y-6 pt-4">
      <div className="space-y-2">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-6 w-1/2" />
        <Skeleton className="h-6 w-2/3" />
      </div>
      <Separator />
      <div className="space-y-4">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
      </div>
      <Separator />
      <div className="space-y-4">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
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
      // Use the new, more accurate skeleton
      return <ViewSkeleton />;
    }
    if (!question) {
      return <div className="text-center py-8">بيانات السؤال غير موجودة.</div>;
    }

    return (
      <div className="space-y-6 pt-4">
        {/* Section 1: Core Details */}
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
          <DetailRow label="المعرف" value={question.id} />
          <DetailRow
            label="الحالة"
            value={
              <Badge variant={question.is_active ? "default" : "outline"}>
                {question.is_active ? "نشط" : "غير نشط"}
              </Badge>
            }
          />
          <DetailRow
            label="مستوى الصعوبة"
            value={difficultyMap[question.difficulty]}
          />
          <DetailRow
            label="إجمالي الاستخدام"
            value={question.total_usage_count}
          />
          <div className="md:col-span-2">
            <DetailRow
              label="التسلسل الهرمي"
              value={`${question.section.name} > ${question.subsection.name} ${
                question.skill ? `> ${question.skill.name}` : ""
              }`}
            />
          </div>
        </dl>

        <Separator />

        {/* Section 2: Question & Answer */}
        <div className="space-y-4">
          <h4 className="font-semibold text-lg">السؤال والخيارات</h4>
          <blockquote className="p-4 bg-muted border-r-4 rtl:border-r-0 rtl:border-l-4 border-primary rounded-r rtl:rounded-r-none rtl:rounded-l">
            {question.question_text}
          </blockquote>
          {question.image && (
            <DetailRow
              label="الصورة"
              value={
                <img
                  src={question.image}
                  alt="صورة السؤال"
                  className="max-w-xs rounded-md border"
                />
              }
            />
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {Object.entries(question.options).map(([key, value]) => (
              <div
                key={key}
                className={`p-3 rounded-md border ${
                  question.correct_answer === key
                    ? "border-green-500 bg-green-50 dark:bg-green-900/20"
                    : ""
                }`}
              >
                <span className="font-bold text-sm text-muted-foreground">
                  الخيار {key}
                </span>
                <p className="font-medium">{value}</p>
              </div>
            ))}
          </div>
        </div>

        <Separator />

        {/* Section 3: Helper Information */}
        <div className="space-y-4">
          <h4 className="font-semibold text-lg">معلومات مساعدة</h4>
          <DetailRow
            label="الشرح"
            value={
              <p className="whitespace-pre-wrap">{question.explanation}</p>
            }
          />
          <DetailRow
            label="تلميح"
            value={<p className="whitespace-pre-wrap">{question.hint}</p>}
          />
          <DetailRow
            label="ملخص الحل"
            value={
              <p className="whitespace-pre-wrap">
                {question.solution_method_summary}
              </p>
            }
          />
        </div>
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>تفاصيل السؤال</DialogTitle>
          <DialogDescription>
            عرض للقراءة فقط للسؤال وبياناته المرتبطة.
          </DialogDescription>
        </DialogHeader>
        {renderContent()}
      </DialogContent>
    </Dialog>
  );
}
