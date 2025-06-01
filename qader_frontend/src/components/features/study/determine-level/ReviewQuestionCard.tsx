"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { CheckCircle, XCircle, Info, BookOpen, Tag, Brain } from "lucide-react";
import {
  Card,
  CardContent,
  // CardFooter, // Not currently used
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
// Ensure UserTestAttemptReviewQuestion is imported from the updated types
import type {
  UserTestAttemptReviewQuestion,
  QuestionOptionKey,
} from "@/types/api/study.types";

interface ReviewQuestionCardProps {
  questionData: UserTestAttemptReviewQuestion;
  questionNumber: number;
  totalQuestionsInFilter: number;
}

const optionKeys: QuestionOptionKey[] = ["A", "B", "C", "D"];

const ReviewQuestionCard: React.FC<ReviewQuestionCardProps> = ({
  questionData,
  questionNumber,
  totalQuestionsInFilter,
}) => {
  const t = useTranslations("Study.determineLevel.review");

  // Destructure based on the updated UserTestAttemptReviewQuestion type
  const {
    question_text,
    choices, // This is where the options are now
    user_answer,
    correct_answer,
    user_is_correct,
    explanation,
    subsection_name,
    skill_name,
  } = questionData;

  const getOptionText = (key: QuestionOptionKey): string => {
    // Access option text from the 'choices' object
    return choices?.[key] || ""; // Use optional chaining for safety, though 'choices' should exist
  };

  const getOptionStyle = (optionKey: QuestionOptionKey) => {
    const isUserSelected = user_answer === optionKey;
    const isActualCorrectAnswer = correct_answer === optionKey;

    if (isUserSelected && user_is_correct) {
      // User selected and it was correct
      return "border-green-500 bg-green-50 dark:bg-green-900/30 ring-2 ring-green-500";
    }
    if (isUserSelected && !user_is_correct && user_answer !== null) {
      // User selected and it was incorrect
      return "border-red-500 bg-red-50 dark:bg-red-900/30 ring-2 ring-red-500";
    }
    // If this option is the correct answer, and the user either skipped or selected something else
    if (isActualCorrectAnswer && (!isUserSelected || user_answer === null)) {
      return "border-green-500 bg-green-50 dark:bg-green-900/30";
    }
    return "border-border"; // Default style for other options
  };

  const getOptionIcon = (optionKey: QuestionOptionKey) => {
    const isUserSelected = user_answer === optionKey;
    const isActualCorrectAnswer = correct_answer === optionKey;

    if (isUserSelected && user_is_correct) {
      return (
        <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-500" />
      );
    }
    if (isUserSelected && !user_is_correct && user_answer !== null) {
      return <XCircle className="h-5 w-5 text-red-600 dark:text-red-500" />;
    }
    // Show a checkmark for the correct answer if it wasn't the user's (incorrect) choice,
    // or if the user skipped.
    if (isActualCorrectAnswer && (!isUserSelected || user_answer === null)) {
      return (
        <CheckCircle className="h-5 w-5 text-green-600 opacity-70 dark:text-green-500" />
      );
    }
    return <span className="h-5 w-5" />; // Placeholder for alignment
  };

  return (
    <Card className="w-full shadow-lg">
      <CardHeader>
        <div className="mb-2 flex items-center justify-between">
          <CardTitle className="text-lg font-semibold md:text-xl">
            {t("questionXofY", {
              current: questionNumber,
              total: totalQuestionsInFilter,
            })}
          </CardTitle>
          {user_answer !== null ? ( // Check if answered
            <Badge
              variant={user_is_correct ? "default" : "destructive"}
              className={cn(
                user_is_correct ? "bg-green-600 hover:bg-green-700" : ""
              )}
            >
              {user_is_correct ? t("correct") : t("incorrect")}
            </Badge>
          ) : (
            // If not answered
            <Badge variant="outline">{t("notAnswered")}</Badge>
          )}
        </div>
        <p className="text-base leading-relaxed text-foreground/90 md:text-lg">
          {question_text}
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          {optionKeys.map((key) => (
            <div
              key={key}
              className={cn(
                "flex items-center space-x-3 rtl:space-x-reverse rounded-md border p-3 transition-all",
                getOptionStyle(key)
              )}
            >
              <div className="flex-shrink-0">{getOptionIcon(key)}</div>
              <span className="font-medium">{key}.</span>
              {/* This will now correctly display the option text */}
              <p className="text-sm md:text-base">{getOptionText(key)}</p>
            </div>
          ))}
        </div>

        {(explanation || subsection_name || skill_name) && (
          <Accordion type="single" collapsible className="w-full pt-4">
            {explanation && (
              <AccordionItem value="explanation">
                <AccordionTrigger className="text-base hover:no-underline">
                  <BookOpen className="me-2 h-5 w-5 text-primary rtl:me-0 rtl:ms-2" />{" "}
                  {t("explanation")}
                </AccordionTrigger>
                <AccordionContent className="prose prose-sm dark:prose-invert max-w-none pt-2 text-base leading-relaxed text-muted-foreground">
                  {explanation}
                </AccordionContent>
              </AccordionItem>
            )}
            {(subsection_name || skill_name) && (
              <AccordionItem
                value="metadata"
                className={
                  explanation && (subsection_name || skill_name)
                    ? ""
                    : "border-b-0"
                }
              >
                {" "}
                {/* Conditional border for aesthetics */}
                <AccordionTrigger className="text-base hover:no-underline">
                  <Info className="me-2 h-5 w-5 text-primary rtl:me-0 rtl:ms-2" />{" "}
                  {t("details")}
                </AccordionTrigger>
                <AccordionContent className="space-y-2 pt-2 text-muted-foreground">
                  {subsection_name && (
                    <div className="flex items-center text-sm">
                      <Tag className="me-2 h-4 w-4 text-sky-600 rtl:me-0 rtl:ms-2" />
                      <strong>{t("subsection")}:</strong>
                      <span className="ms-1 rtl:me-1">{subsection_name}</span>
                    </div>
                  )}
                  {skill_name && (
                    <div className="flex items-center text-sm">
                      <Brain className="me-2 h-4 w-4 text-purple-600 rtl:me-0 rtl:ms-2" />
                      <strong>{t("skill")}:</strong>
                      <span className="ms-1 rtl:me-1">{skill_name}</span>
                    </div>
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
