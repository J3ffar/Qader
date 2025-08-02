"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { CheckCircle, Info, Lightbulb, XCircle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import type { UnifiedQuestion } from "@/types/api/study.types";
import { QuestionState } from "./TraditionalLearningSession";
import { QuestionRenderer } from "@/components/shared/QuestionRenderer";
import { RichContentViewer } from "@/components/shared/RichContentViewer";
import { StarButton } from "@/components/shared/StarButton";

type OptionKey = "A" | "B" | "C" | "D";

const arabicOptionMap: { [key in OptionKey]: string } = {
  A: "أ",
  B: "ب",
  C: "ج",
  D: "د",
};

interface Props {
  question: UnifiedQuestion;
  questionState?: QuestionState;
  onSelectAnswer: (selectedAnswer: OptionKey) => void;
  direction: "ltr" | "rtl";
  attemptId: string;
}

export const QuestionDisplay: React.FC<Props> = ({
  question,
  questionState,
  onSelectAnswer,
  direction,
  attemptId,
}) => {
  const t = useTranslations("Study.traditionalLearning.session");
  const [localStarred, setLocalStarred] = useState(question.is_starred);

  // Update localStarred when question changes
  useEffect(() => {
    setLocalStarred(question.is_starred);
  }, [question.id, question.is_starred]);

  const isAnswered =
    questionState?.status === "correct" ||
    questionState?.status === "incorrect";

  return (
    <Card className="shadow-lg">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
        <div className="flex-1">
          <QuestionRenderer
            questionText={question.question_text}
            imageUrl={question.image}
          />
        </div>
        <div className="flex-shrink-0">
          <StarButton
            questionId={question.id}
            isStarred={localStarred}
            onStarChange={(newState) => setLocalStarred(newState)}
            disabled={isAnswered}
            attemptId={attemptId}
          />
        </div>
      </CardHeader>
      <CardContent>
        <RadioGroup
          value={questionState?.selectedAnswer || ""}
          onValueChange={(value) => onSelectAnswer(value as OptionKey)}
          className="grid grid-cols-1 gap-3 md:grid-cols-2"
          dir={direction}
          disabled={isAnswered}
        >
          {Object.entries(question.options).map(([key, text]) => {
            const optionKey = key as OptionKey;
            const isSelected = questionState?.selectedAnswer === optionKey;
            const isCorrectOption = question.correct_answer === optionKey;
            const isEliminated =
              questionState?.eliminatedOptions?.includes(optionKey);
            const isRevealedAnswer =
              questionState?.revealedAnswer === optionKey;

            let variant: "default" | "correct" | "incorrect" = "default";
            if (isAnswered) {
              if (isCorrectOption) variant = "correct";
              else if (isSelected) variant = "incorrect";
            }

            const uniqueId = `${question.id}-${optionKey}`;

            return (
              <Label
                key={uniqueId} // Using uniqueId for key is also good practice
                htmlFor={uniqueId} // FIX: Use the unique ID
                className={cn(
                  "flex items-center space-x-3 rtl:space-x-reverse rounded-md border p-4 transition-all",
                  // ... rest of the classes are correct
                  isAnswered || isEliminated
                    ? "cursor-not-allowed opacity-60"
                    : "cursor-pointer hover:bg-accent",
                  isEliminated && "bg-muted line-through",
                  isSelected && !isAnswered && "border-primary bg-accent",
                  variant === "correct" &&
                    "border-green-500 bg-green-500/10 opacity-100",
                  variant === "incorrect" &&
                    "border-red-500 bg-red-500/10 opacity-100",
                  isRevealedAnswer &&
                    !isAnswered &&
                    "border-blue-500 ring-2 ring-blue-500 ring-offset-2 dark:ring-offset-background"
                )}
              >
                <RadioGroupItem
                  value={optionKey}
                  id={uniqueId} // FIX: Use the unique ID
                  disabled={isEliminated}
                  className="hidden"
                />
                <div className="flex ml-3 border h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold text-muted-foreground">
                  {arabicOptionMap[optionKey]}
                </div>
                <RichContentViewer
                  htmlContent={text}
                  className="prose dark:prose-invert max-w-none flex-1"
                />
              </Label>
            );
          })}
        </RadioGroup>

        {/* --- Post-Answer Feedback Section --- */}
        {isAnswered && (
          <div className="mt-6 space-y-4">
            <Separator />
            {questionState?.status === "correct" && (
              <Badge variant="default" className="bg-green-600 text-base">
                <CheckCircle className="me-2 h-4 w-4" /> {t("correct")}
              </Badge>
            )}
            {questionState?.status === "incorrect" && (
              <div className="space-y-2">
                <Badge variant="destructive" className="text-base">
                  <XCircle className="me-2 h-4 w-4" />
                  {t("incorrect")}
                </Badge>
                <p className="text-sm text-muted-foreground">
                  {t("correctAnswerWas")}{" "}
                  <strong className="text-foreground">
                    <RichContentViewer
                      htmlContent={
                        question.options[
                          question.correct_answer as keyof typeof question.options
                        ]
                      }
                    />
                  </strong>
                </p>
              </div>
            )}
          </div>
        )}

        {/* --- Revealed Hint/Explanation Section --- */}
        {questionState?.revealedHint && (
          <Alert className="mt-4 border-yellow-500/50 text-yellow-800 dark:text-yellow-300">
            <Lightbulb className="h-5 w-5 !text-yellow-500" />
            <AlertTitle>{t("controls.hint")}</AlertTitle>
            <AlertDescription>
              <RichContentViewer
                htmlContent={questionState.revealedHint}
                className="prose prose-sm dark:prose-invert max-w-none"
              />
            </AlertDescription>
          </Alert>
        )}
        {questionState?.revealedExplanation && (
          <Alert className="mt-4 border-blue-500/50">
            <Info className="h-5 w-5 !text-blue-500" />
            <AlertTitle>{t("explanation")}</AlertTitle>
            <AlertDescription>
              <RichContentViewer
                htmlContent={questionState.revealedExplanation}
                className="prose prose-sm dark:prose-invert max-w-none"
              />
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};
