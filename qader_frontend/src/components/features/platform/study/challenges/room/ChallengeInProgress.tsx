// src/components/features/platform/study/challenges/room/ChallengeInProgress.tsx
"use client";

import { useState, useEffect, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChallengeHeader } from "./ChallengeHeader";
import { ChallengeState } from "@/types/api/challenges.types";
import { submitChallengeAnswer } from "@/services/challenges.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { useAuthCore } from "@/store/auth.store";

type AnswerStatus = "pending" | "correct" | "incorrect" | "idle";

export function ChallengeInProgress({
  challenge,
}: {
  challenge: ChallengeState;
}) {
  const t = useTranslations("Study.challenges");
  const { user } = useAuthCore();
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [answerStatus, setAnswerStatus] = useState<AnswerStatus>("idle");
  const questionStartTimeRef = useRef<number>(Date.now());

  const currentQuestion = challenge.questions[currentQuestionIndex];
  const answeredByUsers = challenge.answeredBy?.[currentQuestion.id] || [];
  const currentUserHasAnswered = answeredByUsers.includes(user?.id ?? 0);

  // Effect to move to next question automatically after a delay
  useEffect(() => {
    if (answerStatus === "correct" || answerStatus === "incorrect") {
      const timer = setTimeout(() => {
        if (currentQuestionIndex < challenge.questions.length - 1) {
          setCurrentQuestionIndex((prev) => prev + 1);
          setSelectedAnswer(null);
          setAnswerStatus("idle");
          questionStartTimeRef.current = Date.now();
        }
      }, 1500); // Wait 1.5s before moving to next
      return () => clearTimeout(timer);
    }
  }, [answerStatus, currentQuestionIndex, challenge.questions.length]);

  const answerMutation = useMutation({
    mutationFn: ({
      answer,
      timeTaken,
    }: {
      answer: string;
      timeTaken: number;
    }) =>
      submitChallengeAnswer(challenge.id, {
        question_id: currentQuestion.id,
        selected_answer: answer,
        time_taken_seconds: timeTaken,
      }),
    onSuccess: (data) => {
      // The WebSocket `answer.result` will give feedback to all players.
      // We use the HTTP response to give immediate feedback to the current user.
      setAnswerStatus(data.is_correct ? "correct" : "incorrect");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, t("errorGeneric")));
      setSelectedAnswer(null);
      setAnswerStatus("idle");
    },
  });

  const handleAnswer = (answer: string) => {
    if (currentUserHasAnswered || answerMutation.isPending) return;
    setSelectedAnswer(answer);
    setAnswerStatus("pending");
    const timeTaken = Math.round(
      (Date.now() - questionStartTimeRef.current) / 1000
    );
    answerMutation.mutate({ answer, timeTaken });
  };

  const getButtonVariant = (
    key: string
  ): "default" | "outline" | "secondary" | "destructive" => {
    if (selectedAnswer === key) {
      if (answerStatus === "correct") return "default"; // Using shadcn's default (green)
      if (answerStatus === "incorrect") return "destructive";
      return "secondary";
    }
    return "outline";
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 animate-fade-in">
      <ChallengeHeader challenge={challenge} />
      <Card>
        <CardHeader>
          <CardTitle className="pt-4 text-center ltr:text-left rtl:text-right">
            {currentQuestionIndex + 1}. {currentQuestion.question_text}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(currentQuestion.options).map(([key, value]) => (
              <Button
                key={key}
                variant={getButtonVariant(key)}
                size="lg"
                className={cn(
                  "h-auto py-4 justify-start text-wrap text-right transition-all",
                  answerStatus === "correct" &&
                    selectedAnswer === key &&
                    "bg-green-500 hover:bg-green-600",
                  answerStatus === "incorrect" &&
                    selectedAnswer === key &&
                    "bg-red-500 hover:bg-red-600"
                )}
                onClick={() => handleAnswer(key)}
                disabled={
                  currentUserHasAnswered ||
                  answerMutation.isPending ||
                  answerStatus !== "idle"
                }
              >
                {answerMutation.isPending && selectedAnswer === key && (
                  <Loader2 className="ltr:mr-2 rtl:ml-2 h-4 w-4 animate-spin" />
                )}
                <span className="font-bold ltr:mr-4 rtl:ml-4">{key}.</span>
                <span className="whitespace-pre-wrap flex-1 ltr:text-left rtl:text-right">
                  {value}
                </span>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
