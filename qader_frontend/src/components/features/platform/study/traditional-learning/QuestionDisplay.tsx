import React from "react";
import { useTranslations } from "next-intl";
import { CheckCircle, XCircle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
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

  // *** THE FIX IS HERE ***
  // Correctly determine if the question has been definitively answered and graded.
  // It's answered only if the status is 'correct' or 'incorrect'.
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
          disabled={isAnswered} // This now works correctly
        >
          {Object.entries(question.options).map(([key, text]) => {
            const optionKey = key as OptionKey;
            const isSelected = questionState?.selectedAnswer === optionKey;
            const isCorrectOption = question.correct_answer === optionKey;

            let variant: "default" | "correct" | "incorrect" = "default";
            if (isAnswered) {
              if (isCorrectOption) {
                variant = "correct";
              } else if (isSelected) {
                // Only mark the selected one as incorrect, not all wrong options
                variant = "incorrect";
              }
            }

            return (
              <Label
                key={optionKey}
                htmlFor={optionKey}
                className={cn(
                  "flex items-center space-x-3 rtl:space-x-reverse rounded-md border p-4 transition-colors",
                  isAnswered
                    ? "cursor-not-allowed"
                    : "cursor-pointer hover:bg-accent",
                  variant === "correct" &&
                    "border-green-500 bg-green-500/10 text-green-900 dark:bg-green-900/30 dark:text-green-300",
                  variant === "incorrect" &&
                    "border-red-500 bg-red-500/10 text-red-900 dark:bg-red-900/30 dark:text-red-300",
                  isSelected && !isAnswered && "border-primary bg-accent"
                )}
              >
                <RadioGroupItem value={optionKey} id={optionKey} />
                <span>{text}</span>
              </Label>
            );
          })}
        </RadioGroup>

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

        {/* This part for revealed explanation via controls remains the same */}
        {questionState?.revealedExplanation && (
          <div className="mt-6 space-y-2 rounded-lg bg-muted/50 p-4">
            <h4 className="font-semibold">{t("explanation")}</h4>
            <p className="text-sm text-muted-foreground">
              {questionState.revealedExplanation}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
