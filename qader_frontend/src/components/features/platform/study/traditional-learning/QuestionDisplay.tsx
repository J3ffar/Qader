import React from "react";
import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { CheckCircle, XCircle } from "lucide-react";
import type { UnifiedQuestion } from "@/types/api/study.types";

type OptionKey = "A" | "B" | "C" | "D";
interface QuestionState {
  status: "unanswered" | "correct" | "incorrect";
  selectedAnswer: OptionKey | null;
  feedback?: string;
  revealedAnswer?: OptionKey;
  revealedExplanation?: string;
}
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
  const isAnswered = questionState?.status !== "unanswered";

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
            const isCorrect = question.correct_answer === optionKey;

            let variant: "default" | "correct" | "incorrect" = "default";
            if (isAnswered) {
              if (isCorrect) variant = "correct";
              else if (isSelected) variant = "incorrect";
            }

            return (
              <Label
                key={optionKey}
                htmlFor={optionKey}
                className={`flex items-center space-x-3 rtl:space-x-reverse rounded-md border p-4 cursor-pointer transition-colors
                ${isAnswered ? "cursor-not-allowed" : "hover:bg-accent"}
                ${
                  variant === "correct"
                    ? "border-green-500 bg-green-500/10"
                    : ""
                }
                ${variant === "incorrect" ? "border-red-500 bg-red-500/10" : ""}
                ${isSelected && !isAnswered ? "border-primary" : ""}
              `}
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
              <Badge variant="default" className="text-base">
                <CheckCircle className="me-2 h-4 w-4" /> {t("correct")}
              </Badge>
            )}
            {questionState?.status === "incorrect" && (
              <div className="space-y-2">
                <Badge variant="destructive" className="text-base">
                  <XCircle className="me-2 h-4 w-4" />
                  {t("incorrect")}
                </Badge>
                <p className="text-sm">
                  {t("correctAnswerWas")}{" "}
                  <strong>{question.options[question.correct_answer]}</strong>
                </p>
              </div>
            )}
          </div>
        )}

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
