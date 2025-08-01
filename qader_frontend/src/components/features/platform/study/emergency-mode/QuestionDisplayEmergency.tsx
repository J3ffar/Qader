"use client";

import React, { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2, X } from "lucide-react";
import { toast } from "sonner";

import { useEmergencyModeStore } from "@/store/emergency.store";
import { submitEmergencyAnswer } from "@/services/study.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

import { cn } from "@/lib/utils";
import {
  UnifiedQuestion,
  EmergencyModeAnswerResponse,
} from "@/types/api/study.types";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { queryKeys } from "@/constants/queryKeys";
import { QuestionRenderer } from "@/components/shared/QuestionRenderer";
import { RichContentViewer } from "@/components/shared/RichContentViewer";

type AnswerOption = "A" | "B" | "C" | "D";

const arabicOptionMap: { [key in AnswerOption]: string } = {
  A: "أ",
  B: "ب",
  C: "ج",
  D: "د",
};

interface QuestionDisplayEmergencyProps {
  question: UnifiedQuestion;
  currentQuestionNumber: number;
  totalQuestions: number;
  isLastQuestion: boolean;
  onLastAnswered: () => void;
}

export function QuestionDisplayEmergency({
  question,
  currentQuestionNumber,
  totalQuestions,
  isLastQuestion,
  onLastAnswered,
}: QuestionDisplayEmergencyProps) {
  const t = useTranslations("Study.emergencyMode.session.question");
  const { sessionId, goToNextQuestion } = useEmergencyModeStore();

  const [selectedAnswer, setSelectedAnswer] = useState<AnswerOption | null>(
    null
  );
  const [isAnswered, setIsAnswered] = useState(false);
  const [feedback, setFeedback] = useState<EmergencyModeAnswerResponse | null>(
    null
  );

  // Reset component state when a new question is passed in
  useEffect(() => {
    setSelectedAnswer(null);
    setIsAnswered(false);
    setFeedback(null);
  }, [question.id]);

  const { mutate: submitAnswer, isPending } = useMutation({
    mutationKey: queryKeys.emergencyMode.submitAnswer(
      sessionId as number,
      question.id
    ),
    mutationFn: (answer: AnswerOption) =>
      submitEmergencyAnswer({
        sessionId: sessionId!,
        payload: { question_id: question.id, selected_answer: answer },
      }),
    onSuccess: (data) => {
      setFeedback(data);
      setIsAnswered(true);
    },
    onError: (error) => {
      toast.error(t("submitErrorToast"), {
        description: getApiErrorMessage(error, t("submitErrorToast")),
      });
    },
  });

  const handleSubmit = () => {
    if (selectedAnswer) {
      submitAnswer(selectedAnswer);
    }
  };

  const handleNext = () => {
    // UPDATED LOGIC HERE
    if (isLastQuestion) {
      onLastAnswered();
    } else {
      goToNextQuestion();
    }
  };

  const options = Object.entries(question.options) as [AnswerOption, string][];

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>
          {t("progress", {
            current: currentQuestionNumber,
            total: totalQuestions,
          })}
        </CardDescription>
        <QuestionRenderer
          questionText={question.question_text}
          imageUrl={question.image}
        />
      </CardHeader>
      <CardContent>
        <RadioGroup
          value={selectedAnswer ?? undefined}
          onValueChange={(value: AnswerOption) => setSelectedAnswer(value)}
          disabled={isAnswered || isPending}
          className="space-y-3"
          dir={"rtl"}
        >
          {options.map(([key, value]) => {
            const isSelected = selectedAnswer === key;
            const isCorrect = feedback?.correct_answer === key;
            const wasCorrectlyAnswered = feedback?.is_correct;

            return (
              <div
                key={key}
                className={cn(
                  "flex items-center space-x-3 rtl:space-x-reverse rounded-md border p-4 transition-all",
                  "data-[state=checked]:border-primary data-[state=checked]:ring-1 data-[state=checked]:ring-primary",
                  isAnswered && isCorrect && "border-green-500 bg-green-500/10",
                  isAnswered &&
                    isSelected &&
                    !wasCorrectlyAnswered &&
                    "border-red-500 bg-red-500/10",
                  !isAnswered && "cursor-pointer hover:bg-accent"
                )}
                data-state={isSelected ? "checked" : "unchecked"}
                onClick={() =>
                  !(isAnswered || isPending) && setSelectedAnswer(key)
                }
              >
                <RadioGroupItem
                  value={key}
                  id={`option-${key}`}
                  className="hidden"
                />
                <div className="flex ml-3 border h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold text-muted-foreground">
                  {arabicOptionMap[key]}
                </div>
                <RichContentViewer
                  htmlContent={value}
                  className="prose dark:prose-invert max-w-none flex-1"
                />
              </div>
            );
          })}
        </RadioGroup>
      </CardContent>
      <CardFooter className="flex-col items-stretch space-y-4">
        <AnimatePresence>
          {isAnswered && feedback && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <Alert
                variant={feedback.is_correct ? "default" : "destructive"}
                className={cn(feedback.is_correct && "border-green-500")}
              >
                {feedback.is_correct ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <X className="h-4 w-4" />
                )}
                <AlertTitle>{feedback.feedback}</AlertTitle>
                {feedback.explanation && (
                  <AlertDescription className="mt-2">
                    {feedback.explanation}
                  </AlertDescription>
                )}
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>

        {!isAnswered ? (
          <Button
            onClick={handleSubmit}
            disabled={!selectedAnswer || isPending}
            className="w-full"
          >
            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {t("submitButton")}
          </Button>
        ) : (
          <Button onClick={handleNext} className="w-full">
            {t("nextButton")}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
