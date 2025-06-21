"use client";

import { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ChallengeDetail } from "@/types/api/challenges.types";
import { submitChallengeAnswer } from "@/services/challenges.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

export function ChallengeInProgress({
  challenge,
}: {
  challenge: ChallengeDetail;
}) {
  const t = useTranslations("Study.challenges");
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);

  const currentQuestion = challenge.questions[currentQuestionIndex];

  const answerMutation = useMutation({
    mutationFn: (answer: string) =>
      submitChallengeAnswer(challenge.id, {
        question_id: currentQuestion.id,
        selected_answer: answer,
      }),
    onSuccess: () => {
      // The WebSocket 'answer.result' will give toast feedback
      // Move to next question after a short delay
      setTimeout(() => {
        if (currentQuestionIndex < challenge.questions.length - 1) {
          setCurrentQuestionIndex((prev) => prev + 1);
          setSelectedAnswer(null);
        }
      }, 1000);
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, t("errorGeneric"))),
  });

  const handleAnswer = (answer: string) => {
    setSelectedAnswer(answer);
    answerMutation.mutate(answer);
  };

  // A very basic timer example
  const [timeLeft, setTimeLeft] = useState(30);
  useEffect(() => {
    const timer = setInterval(
      () => setTimeLeft((t) => (t > 0 ? t - 1 : 0)),
      1000
    );
    return () => clearInterval(timer);
  }, [currentQuestionIndex]);

  return (
    <Card className="w-full max-w-2xl mx-auto animate-fade-in">
      <CardHeader>
        <CardDescription className="text-center">
          {t("question")} {currentQuestionIndex + 1} /{" "}
          {challenge.questions.length}
        </CardDescription>
        <Progress
          value={
            ((currentQuestionIndex + 1) / challenge.questions.length) * 100
          }
          className="mt-2"
        />
        <CardTitle className="pt-4 text-center">
          {currentQuestion.question_text}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {["A", "B", "C", "D"].map((option) => (
            <Button
              key={option}
              variant={selectedAnswer === option ? "default" : "outline"}
              size="lg"
              className="h-auto py-4 text-right justify-start"
              onClick={() => handleAnswer(option)}
              disabled={!!selectedAnswer || answerMutation.isPending}
            >
              {answerMutation.isPending && selectedAnswer === option && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              <span className="font-bold mr-4">{option}.</span>
              <span className="whitespace-pre-wrap">
                {
                  currentQuestion.options[
                    option as keyof typeof currentQuestion.options
                  ]
                }
              </span>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
