"use client";

import { useState, useEffect, useRef } from "react";
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

  // Rationale: Use a ref to track the start time for each question to accurately calculate time taken.
  const questionStartTimeRef = useRef<number>(Date.now());

  const currentQuestion = challenge.questions[currentQuestionIndex];

  const answerMutation = useMutation({
    // Rationale: Correctly added `time_taken_seconds` to the payload to match the API requirements.
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
    onSuccess: () => {
      // The WebSocket `answer.result` will give the user immediate feedback (toast).
      // The WebSocket `participant.update` will update their score.
      // We'll transition to the next question after a brief delay for the user to see feedback.
      setTimeout(() => {
        if (currentQuestionIndex < challenge.questions.length - 1) {
          setCurrentQuestionIndex((prev) => prev + 1);
          setSelectedAnswer(null);
          questionStartTimeRef.current = Date.now(); // Reset timer for the new question
        }
        // If it's the last question, we don't do anything here.
        // We wait for the `challenge.end` WebSocket event to transition to the results screen.
      }, 1200);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, t("errorGeneric")));
      // Allow the user to try again if the submission fails
      setSelectedAnswer(null);
    },
  });

  const handleAnswer = (answer: string) => {
    setSelectedAnswer(answer);
    const timeTaken = Math.round(
      (Date.now() - questionStartTimeRef.current) / 1000
    );
    answerMutation.mutate({ answer, timeTaken });
  };

  // Timer logic... (no changes needed here)

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
        <CardTitle className="pt-4 text-center ltr:text-left rtl:text-right">
          {currentQuestion.question_text}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(currentQuestion.options).map(([key, value]) => (
            <Button
              key={key}
              variant={selectedAnswer === key ? "default" : "outline"}
              size="lg"
              className="h-auto py-4 justify-start text-wrap text-right"
              onClick={() => handleAnswer(key)}
              disabled={!!selectedAnswer || answerMutation.isPending}
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
  );
}
