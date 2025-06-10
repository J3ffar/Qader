// src/components/features/platform/study/determine-level/ReviewQuestionCard.tsx

"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { CheckCircle, XCircle, HelpCircle, Info, Brain } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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

interface ReviewQuestionCardProps {
  questionData: UnifiedQuestion;
  questionNumber: number;
  totalQuestionsInFilter: number;
}

const ReviewQuestionCard: React.FC<ReviewQuestionCardProps> = ({
  questionData,
  questionNumber,
  totalQuestionsInFilter,
}) => {
  const t = useTranslations("Study.determineLevel.review");
  const tCommon = useTranslations("Common");

  // --- REFACTORED: Data destructured from the new UnifiedQuestion type ---
  const {
    id: questionId,
    question_text,
    options,
    correct_answer,
    explanation,
    subsection,
    skill,
    user_answer_details,
  } = questionData;

  const user_selected_choice = user_answer_details?.selected_choice;
  const user_is_correct = user_answer_details?.is_correct;

  const getOptionStatus = (optionKey: keyof typeof options) => {
    const isSelected = user_selected_choice === optionKey;
    const isCorrect = correct_answer === optionKey;

    if (isSelected && isCorrect) return "selectedCorrect";
    if (isSelected && !isCorrect) return "selectedIncorrect";
    if (!isSelected && isCorrect) return "correctUnselected";
    return "default";
  };

  const statusIndicator = () => {
    if (user_selected_choice === null) {
      return (
        <Badge
          variant="outline"
          className="border-amber-400 bg-amber-50 text-amber-700 dark:border-amber-600 dark:bg-amber-900/30 dark:text-amber-400"
        >
          <HelpCircle className="me-1.5 h-4 w-4 rtl:me-0 rtl:ms-1.5" />
          {t("statusSkipped")}
        </Badge>
      );
    }
    if (user_is_correct) {
      return (
        <Badge
          variant="outline"
          className="border-green-400 bg-green-50 text-green-700 dark:border-green-600 dark:bg-green-900/30 dark:text-green-400"
        >
          <CheckCircle className="me-1.5 h-4 w-4 rtl:me-0 rtl:ms-1.5" />
          {t("statusCorrect")}
        </Badge>
      );
    }
    return (
      <Badge
        variant="outline"
        className="border-red-400 bg-red-50 text-red-700 dark:border-red-600 dark:bg-red-900/30 dark:text-red-400"
      >
        <XCircle className="me-1.5 h-4 w-4 rtl:me-0 rtl:ms-1.5" />
        {t("statusIncorrect")}
      </Badge>
    );
  };

  return (
    <Card
      className="w-full shadow-lg"
      data-testid={`question-card-${questionId}`}
    >
      <CardHeader>
        <div className="mb-3 flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between">
          <CardDescription className="text-sm font-semibold text-primary">
            {t("questionXofY", {
              current: questionNumber,
              total: totalQuestionsInFilter,
            })}
          </CardDescription>
          {statusIndicator()}
        </div>
        <CardTitle
          className="text-lg leading-relaxed rtl:text-right md:text-xl"
          dir="auto"
        >
          {question_text}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Separator />
        <div className="space-y-3">
          {/* REFACTORED: Iterate over the `options` object directly */}
          {(Object.keys(options) as Array<keyof typeof options>).map((key) => {
            const optionText = options[key];
            if (optionText === undefined || optionText === null) return null;

            const status = getOptionStatus(key);
            let statusIcon = null;
            let ringClass = "ring-border";
            let textClass = "text-foreground";
            let bgClass = "bg-card hover:bg-muted/50";
            let optionIndicatorClass = "text-muted-foreground";

            if (status === "selectedCorrect") {
              statusIcon = (
                <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-500" />
              );
              ringClass = "ring-2 ring-green-500 dark:ring-green-600";
              textClass = "text-green-700 dark:text-green-400";
              bgClass = "bg-green-50 dark:bg-green-900/40";
              optionIndicatorClass = "text-green-700 dark:text-green-400";
            } else if (status === "selectedIncorrect") {
              statusIcon = (
                <XCircle className="h-5 w-5 text-red-600 dark:text-red-500" />
              );
              ringClass = "ring-2 ring-red-500 dark:ring-red-600";
              textClass = "text-red-700 dark:text-red-400";
              bgClass = "bg-red-50 dark:bg-red-900/40";
              optionIndicatorClass = "text-red-700 dark:text-red-400";
            } else if (status === "correctUnselected") {
              statusIcon = (
                <CheckCircle className="h-5 w-5 text-green-600 opacity-70 dark:text-green-500" />
              );
              bgClass = "bg-green-50/70 dark:bg-green-900/30";
              optionIndicatorClass = "text-green-600 dark:text-green-500";
            }

            return (
              <div
                key={key}
                className={cn(
                  "flex items-start space-x-3 rtl:space-x-reverse rounded-md border p-3.5 transition-all",
                  bgClass,
                  ringClass
                )}
                dir="auto"
              >
                {statusIcon ? (
                  <span className="mt-0.5 flex-shrink-0">{statusIcon}</span>
                ) : (
                  <span className="mt-0.5 h-5 w-5 flex-shrink-0"></span>
                )}
                <span className={cn("font-semibold", optionIndicatorClass)}>
                  {key}.
                </span>
                <p className={cn("flex-1 text-base", textClass)}>
                  {optionText}
                </p>
              </div>
            );
          })}
        </div>

        {(explanation || subsection?.name || skill?.name) && (
          <Accordion type="multiple" className="w-full pt-3">
            {explanation && (
              <AccordionItem value="explanation">
                <AccordionTrigger className="text-base font-medium hover:no-underline">
                  <Info className="me-2 h-5 w-5 text-blue-500 rtl:me-0 rtl:ms-2" />
                  {t("explanation")}
                </AccordionTrigger>
                <AccordionContent
                  className="pt-2 text-base leading-relaxed text-muted-foreground"
                  dir="auto"
                >
                  {explanation}
                </AccordionContent>
              </AccordionItem>
            )}
            {/* REFACTORED: Use new data structure for details */}
            {(subsection?.name || skill?.name) && (
              <AccordionItem value="details">
                <AccordionTrigger className="text-base font-medium hover:no-underline">
                  <Brain className="me-2 h-5 w-5 text-purple-500 rtl:me-0 rtl:ms-2" />
                  {t("details")}
                </AccordionTrigger>
                <AccordionContent className="space-y-2 pt-2 text-base text-muted-foreground">
                  {subsection?.name && (
                    <p dir="auto">
                      <span className="font-semibold text-foreground">
                        {t("subsection")}:
                      </span>{" "}
                      {subsection.name}
                    </p>
                  )}
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
            )}
          </Accordion>
        )}
      </CardContent>
    </Card>
  );
};

export default ReviewQuestionCard;
