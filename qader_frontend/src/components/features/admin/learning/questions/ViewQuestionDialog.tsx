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
    <dd className="text-sm col-span-2">{value ?? "N/A"}</dd>
  </div>
);

const difficultyMap: { [key: number]: string } = {
  1: "1 - Very Easy",
  2: "2 - Easy",
  3: "3 - Medium",
  4: "4 - Hard",
  5: "5 - Very Hard",
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
      return <div className="text-center py-8">Question data not found.</div>;
    }

    return (
      <div className="space-y-4 pt-4">
        <dl className="space-y-2">
          <DetailRow label="ID" value={question.id} />
          <DetailRow
            label="Status"
            value={
              <Badge variant={question.is_active ? "default" : "outline"}>
                {question.is_active ? "Active" : "Inactive"}
              </Badge>
            }
          />
          <DetailRow
            label="Hierarchy"
            value={`${question.section.name} > ${question.subsection.name} ${
              question.skill ? `> ${question.skill.name}` : ""
            }`}
          />
          <DetailRow
            label="Difficulty"
            value={difficultyMap[question.difficulty]}
          />
        </dl>

        <Separator />

        <div className="space-y-4">
          <h4 className="font-semibold">Question & Options</h4>
          <p className="p-3 bg-muted rounded-md text-sm">
            {question.question_text}
          </p>
          <DetailRow label="Option A" value={question.options.A} />
          <DetailRow label="Option B" value={question.options.B} />
          <DetailRow label="Option C" value={question.options.C} />
          <DetailRow label="Option D" value={question.options.D} />
          <DetailRow
            label="Correct Answer"
            value={
              <Badge variant="secondary">
                Option {question.correct_answer}
              </Badge>
            }
          />
          {question.image && (
            <DetailRow
              label="Image"
              value={
                <img
                  src={question.image}
                  alt="Question image"
                  className="max-w-xs rounded-md border"
                />
              }
            />
          )}
        </div>

        <Separator />

        <div className="space-y-4">
          <h4 className="font-semibold">Supporting Info</h4>
          <DetailRow
            label="Explanation"
            value={question.explanation || "None provided"}
          />
          <DetailRow label="Hint" value={question.hint || "None provided"} />
          <DetailRow
            label="Solution Summary"
            value={question.solution_method_summary || "None provided"}
          />
        </div>

        <Separator />

        <div className="space-y-4">
          <h4 className="font-semibold">Usage Statistics</h4>
          <DetailRow
            label="Total Attempts"
            value={question.total_usage_count}
          />
          {question.usage_by_test_type &&
            Object.entries(question.usage_by_test_type).map(([key, value]) => (
              <DetailRow
                key={key}
                label={key
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase())}
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
          <DialogTitle>Question Details</DialogTitle>
          <DialogDescription>
            A read-only view of the question and its associated data.
          </DialogDescription>
        </DialogHeader>
        {renderContent()}
      </DialogContent>
    </Dialog>
  );
}
