"use client";

import { useState, useEffect } from "react";
import { useTranslations, useLocale } from "next-intl";
import {
  CheckCircle,
  XCircle,
  HelpCircle,
  Info,
  Brain,
  BookText,
} from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { UnifiedQuestion } from "@/types/api/study.types";
import { RichContentViewer } from "./RichContentViewer";
import { QuestionRenderer } from "./QuestionRenderer";
import { StarButton } from "./StarButton";

interface ReviewQuestionCardProps {
  questionData: UnifiedQuestion;
  questionNumber: number;
  totalQuestionsInFilter: number;
  attemptId: string;
}

type OptionKey = "A" | "B" | "C" | "D";

const arabicOptionMap: { [key in OptionKey]: string } = {
  A: "أ",
  B: "ب",
  C: "ج",
  D: "د",
};

const ReviewQuestionCard: React.FC<ReviewQuestionCardProps> = ({
  questionData,
  questionNumber,
  totalQuestionsInFilter,
  attemptId,
}) => {
  const t = useTranslations("Study.review");
  const locale = useLocale();
  const [localStarred, setLocalStarred] = useState(questionData.is_starred);

  // Update localStarred when question changes
  useEffect(() => {
    setLocalStarred(questionData.is_starred);
  }, [questionData.id, questionData.is_starred]);

  const {
    question_text,
    image,
    options,
    correct_answer,
    explanation,
    solution_method_summary,
    section,
    subsection,
    skill,
    user_answer_details,
  } = questionData;

  const user_selected_choice = user_answer_details?.selected_choice;
  const is_correct = user_answer_details?.is_correct;

  const getStatusInfo = () => {
    if (is_correct === true) {
      return {
        text: t("statusCorrect"),
        Icon: CheckCircle,
        className:
          "border-green-400 bg-green-50 text-green-700 dark:border-green-600 dark:bg-green-900/30 dark:text-green-400",
      };
    }
    if (is_correct === false) {
      return {
        text: t("statusIncorrect"),
        Icon: XCircle,
        className:
          "border-red-400 bg-red-50 text-red-700 dark:border-red-600 dark:bg-red-900/30 dark:text-red-400",
      };
    }
    return {
      text: t("statusSkipped"),
      Icon: HelpCircle,
      className:
        "border-amber-400 bg-amber-50 text-amber-700 dark:border-amber-600 dark:bg-amber-900/30 dark:text-amber-400",
    };
  };

  const getOptionStyle = (optionKey: OptionKey) => {
    if (optionKey === correct_answer) {
      return "border-green-500 ring-2 ring-green-500/80 bg-green-500/10";
    }
    if (optionKey === user_selected_choice && optionKey !== correct_answer) {
      return "border-red-500 ring-2 ring-red-500/80 bg-red-500/10";
    }
    return "border-border";
  };

  const statusInfo = getStatusInfo();
  const StatusIcon = statusInfo.Icon;

  return (
    <Card
      dir={locale === "en" ? "ltr" : "rtl"}
      className="w-full shadow-lg dark:bg-[#0B1739] border-2 dark:border-[#7E89AC]"
      data-testid={`question-card-${questionData.id}`}
    >
      <CardHeader>
        <div className="mb-3 flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm font-semibold text-primary">
            {t("questionXofY", {
              current: questionNumber,
              total: totalQuestionsInFilter,
            })}
          </p>
          <Badge
            variant="outline"
            className={cn("text-sm", statusInfo.className)}
          >
            <StatusIcon className="me-1.5 h-4 w-4" />
            {statusInfo.text}
          </Badge>
        </div>
        <div className="flex items-start gap-4">
          <div className="flex-1">
            <QuestionRenderer questionText={question_text} imageUrl={image} />
          </div>
          <div className="flex-shrink-0 pt-2">
            <StarButton
              questionId={questionData.id}
              isStarred={localStarred}
              onStarChange={(newState) => setLocalStarred(newState)}
              disabled={false}
              attemptId={attemptId}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Separator />
        <div className="space-y-3">
          {(Object.keys(options) as OptionKey[]).map((key) => (
            <div
              key={key}
              className={cn(
                "flex items-start space-x-3 rounded-md border p-3.5 transition-all",
                getOptionStyle(key)
              )}
            >
              <div className="mt-0.5 ml-3 border flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-muted font-sans text-sm font-semibold text-muted-foreground">
                {arabicOptionMap[key]}
              </div>
              <RichContentViewer
                htmlContent={options[key]}
                className="prose dark:prose-invert max-w-none flex-1 text-base"
              />
              {key === user_selected_choice && (
                <Badge variant="outline" className="flex-shrink-0 text-xs">
                  {t("yourAnswer")}
                </Badge>
              )}
            </div>
          ))}
        </div>

        <Accordion type="multiple" className="w-full space-y-2 pt-2">
          {explanation && (
            <AccordionItem
              value="explanation"
              className="rounded-md border bg-blue-500/5 dark:bg-blue-500/10"
            >
              <AccordionTrigger className="px-4 py-3 text-base font-semibold text-blue-700 hover:no-underline dark:text-blue-300">
                <Info className="me-2 h-5 w-5" />
                {t("explanation")}
              </AccordionTrigger>
              <AccordionContent className="px-4 pb-4">
                <RichContentViewer
                  htmlContent={explanation}
                  className="prose dark:prose-invert max-w-none text-base leading-relaxed"
                />
              </AccordionContent>
            </AccordionItem>
          )}
          {solution_method_summary && (
            <AccordionItem
              value="solution"
              className="rounded-md border bg-indigo-500/5 dark:bg-indigo-500/10"
            >
              <AccordionTrigger className="px-4 py-3 text-base font-semibold text-indigo-700 hover:no-underline dark:text-indigo-300">
                <BookText className="me-2 h-5 w-5" />
                {t("solutionMethod")}
              </AccordionTrigger>
              <AccordionContent className="px-4 pb-4">
                <RichContentViewer
                  htmlContent={solution_method_summary}
                  className="prose dark:prose-invert max-w-none text-base leading-relaxed"
                />
              </AccordionContent>
            </AccordionItem>
          )}
          <AccordionItem
            value="details"
            className="rounded-md border bg-gray-500/5 dark:bg-gray-500/10"
          >
            <AccordionTrigger className="px-4 py-3 text-base font-semibold text-gray-700 hover:no-underline dark:text-gray-300">
              <Brain className="me-2 h-5 w-5" />
              {t("details")}
            </AccordionTrigger>
            <AccordionContent className="space-y-2 px-4 pb-4 pt-2 text-base text-muted-foreground">
              <p dir="auto">
                <span className="font-semibold text-foreground">
                  {t("section")}:
                </span>{" "}
                {section.name}
              </p>
              <p dir="auto">
                <span className="font-semibold text-foreground">
                  {t("subsection")}:
                </span>{" "}
                {subsection.name}
              </p>
              {skill?.name && (
                <p dir="auto">
                  <span className="font-semibold text-foreground">
                    {t("skill")}:
                  </span>{" "}
                  {skill.name}
                </p>
              )}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  );
};

export default ReviewQuestionCard;
