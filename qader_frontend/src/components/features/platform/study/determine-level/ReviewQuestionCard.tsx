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
import type {
  UserTestAttemptReviewQuestion,
  QuestionOptionKey,
} from "@/types/api/study.types";

interface ReviewQuestionCardProps {
  questionData: UserTestAttemptReviewQuestion;
  questionNumber: number;
  totalQuestionsInFilter: number;
}

const OPTION_KEYS: QuestionOptionKey[] = ["A", "B", "C", "D"]; // Assuming up to D

const ReviewQuestionCard: React.FC<ReviewQuestionCardProps> = ({
  questionData,
  questionNumber,
  totalQuestionsInFilter,
}) => {
  const t = useTranslations("Study.determineLevel.review");
  const tCommon = useTranslations("Common");

  const {
    question_text,
    options,
    user_selected_choice, // Renamed from user_answer to match API response
    correct_answer_choice, // Renamed from correct_answer
    user_is_correct,
    explanation,
    subsection_name,
    skill_name,
  } = questionData;

  const getOptionStatus = (optionKey: QuestionOptionKey) => {
    const isSelected = user_selected_choice === optionKey;
    const isCorrect = correct_answer_choice === optionKey;

    if (isSelected && isCorrect) return "selectedCorrect";
    if (isSelected && !isCorrect) return "selectedIncorrect";
    if (!isSelected && isCorrect) return "correctUnselected"; // Correct answer, but user didn't pick it
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
      data-testid={`question-card-${questionData.question_id}`}
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
          {OPTION_KEYS.map((key) => {
            const optionText = options[key];
            // Check if the option exists in the question's options object
            if (optionText === undefined || optionText === null) return null;

            const status = getOptionStatus(key);
            let statusIcon = null;
            let ringClass = "ring-border"; // Default ring
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
              // Highlight the correct answer even if not selected by the user
              statusIcon = (
                <CheckCircle className="h-5 w-5 text-green-600 opacity-70 dark:text-green-500" />
              );
              bgClass = "bg-green-50/70 dark:bg-green-900/30"; // More subtle highlight
              // ringClass = "ring-1 ring-green-400 dark:ring-green-700"; // Subtle ring
              // textClass = "text-green-700 dark:text-green-500"; // Make text slightly different
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
                  // Placeholder for alignment if no icon (e.g. default unselected options)
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

        {(explanation || subsection_name || skill_name) && (
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
            {(subsection_name || skill_name) && (
              <AccordionItem value="details">
                <AccordionTrigger className="text-base font-medium hover:no-underline">
                  <Brain className="me-2 h-5 w-5 text-purple-500 rtl:me-0 rtl:ms-2" />
                  {t("details")}
                </AccordionTrigger>
                <AccordionContent className="space-y-2 pt-2 text-base text-muted-foreground">
                  {subsection_name && (
                    <p dir="auto">
                      <span className="font-semibold text-foreground">
                        {t("subsection")}:
                      </span>{" "}
                      {subsection_name}
                    </p>
                  )}
                  {skill_name && (
                    <p dir="auto">
                      <span className="font-semibold text-foreground">
                        {t("skill")}:
                      </span>{" "}
                      {skill_name}
                    </p>
                  )}
                  {!subsection_name && !skill_name && (
                    <p>{tCommon("status.notAvailable")}</p>
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
