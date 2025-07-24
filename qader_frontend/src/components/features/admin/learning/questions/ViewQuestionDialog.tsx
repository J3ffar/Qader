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
      return (
        <div className="space-y-4 pt-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      );
    }
    if (!question) {
      return <div className="text-center py-8">بيانات السؤال غير موجودة.</div>;
    }

    return (
      <div className="space-y-4 pt-4">
        <dl className="space-y-2">
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
            label="التسلسل الهرمي"
            value={`${question.section.name} > ${question.subsection.name} ${
              question.skill ? `> ${question.skill.name}` : ""
            }`}
          />
          <DetailRow
            label="مستوى الصعوبة"
            value={difficultyMap[question.difficulty]}
          />
        </dl>

        <Separator />

        <div className="space-y-4">
          <h4 className="font-semibold">السؤال والخيارات</h4>
          <p className="p-3 bg-muted rounded-md text-sm">
            {question.question_text}
          </p>
          <DetailRow label="الخيار أ" value={question.options.A} />
          <DetailRow label="الخيار ب" value={question.options.B} />
          <DetailRow label="الخيار ج" value={question.options.C} />
          <DetailRow label="الخيار د" value={question.options.D} />
          <DetailRow
            label="الإجابة الصحيحة"
            value={
              <Badge variant="secondary">
                الخيار {question.correct_answer}
              </Badge>
            }
          />
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
        </div>

        <Separator />

        <div className="space-y-4">
          <h4 className="font-semibold">معلومات مساعدة</h4>
          <DetailRow label="الشرح" value={question.explanation} />
          <DetailRow label="تلميح" value={question.hint} />
          <DetailRow
            label="ملخص الحل"
            value={question.solution_method_summary}
          />
        </div>

        <Separator />

        <div className="space-y-4">
          <h4 className="font-semibold">إحصائيات الاستخدام</h4>
          <DetailRow
            label="إجمالي المحاولات"
            value={question.total_usage_count}
          />
          {question.usage_by_test_type &&
            Object.entries(question.usage_by_test_type).map(([key, value]) => (
              <DetailRow
                key={key}
                label={key
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase())} // This part can be improved with a proper translation map if needed
                value={value}
              />
            ))}
        </div>
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
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
