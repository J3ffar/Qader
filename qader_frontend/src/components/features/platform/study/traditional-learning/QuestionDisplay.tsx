import React from "react";
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
import { QuestionState } from "./TraditionalLearningSession"; // Import the shared type

type OptionKey = "A" | "B" | "C" | "D";

interface Props {
  question: UnifiedQuestion;
  questionState?: QuestionState;
  onSelectAnswer: (selectedAnswer: OptionKey) => void;
  direction: "ltr" | "rtl";
}

export const QuestionDisplay: React.FC<Props> = ({
  question,
  questionState,
  onSelectAnswer,
  direction,
}) => {
  const t = useTranslations("Study.traditionalLearning.session");

  const isAnswered =
    questionState?.status === "correct" ||
    questionState?.status === "incorrect";

  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle className="text-right text-lg leading-relaxed rtl:text-right">
          {question.question_text}
        </CardTitle>
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
            // NEW: Check if this option was eliminated by the tool
            const isEliminated =
              questionState?.eliminatedOptions?.includes(optionKey);
            // NEW: Check if this option should be highlighted as the revealed correct answer
            const isRevealedAnswer =
              questionState?.revealedAnswer === optionKey;

            let variant: "default" | "correct" | "incorrect" = "default";
            if (isAnswered) {
              if (isCorrectOption) variant = "correct";
              else if (isSelected) variant = "incorrect";
            }

            return (
              <Label
                key={optionKey}
                htmlFor={optionKey}
                className={cn(
                  "flex items-center space-x-3 rtl:space-x-reverse rounded-md border p-4 transition-all",
                  // Base styles for interactivity
                  isAnswered || isEliminated
                    ? "cursor-not-allowed opacity-60"
                    : "cursor-pointer hover:bg-accent",
                  // Style for eliminated option
                  isEliminated && "bg-muted line-through",
                  // Style for selected but not-yet-graded option
                  isSelected && !isAnswered && "border-primary bg-accent",
                  // Graded styles
                  variant === "correct" &&
                    "border-green-500 bg-green-500/10 opacity-100",
                  variant === "incorrect" &&
                    "border-red-500 bg-red-500/10 opacity-100",
                  // Style for revealed correct answer (before answering)
                  isRevealedAnswer &&
                    !isAnswered &&
                    "border-blue-500 ring-2 ring-blue-500 ring-offset-2 dark:ring-offset-background"
                )}
              >
                <RadioGroupItem
                  value={optionKey}
                  id={optionKey}
                  disabled={isEliminated} // Directly disable the input
                />
                <span>{text}</span>
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
                    {question.options[question.correct_answer]}
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
            <AlertDescription>{questionState.revealedHint}</AlertDescription>
          </Alert>
        )}
        {questionState?.revealedExplanation && (
          <Alert className="mt-4 border-blue-500/50">
            <Info className="h-5 w-5 !text-blue-500" />
            <AlertTitle>{t("explanation")}</AlertTitle>
            <AlertDescription>
              {questionState.revealedExplanation}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};
