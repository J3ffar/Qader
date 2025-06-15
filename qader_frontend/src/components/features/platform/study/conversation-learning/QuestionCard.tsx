"use client";

import React from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useTranslations } from "next-intl";
import { AlertTriangle } from "lucide-react";

import * as convoService from "@/services/conversation.service";
import { useConversationStore } from "@/store/conversation.store";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { ConversationTestResult } from "@/types/api/conversation.types";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Loader2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { UnifiedQuestion } from "@/types/api/study.types";

interface QuestionCardProps {
  question: UnifiedQuestion; // This can now potentially be incomplete
  isTestMode: boolean;
  testResult?: ConversationTestResult;
}

export function QuestionCard({
  question,
  isTestMode,
  testResult,
}: QuestionCardProps) {
  const t = useTranslations("study.conversationalLearning");
  const { sessionId, addMessage, setCurrentTestQuestion } =
    useConversationStore();
  const [selectedOption, setSelectedOption] = React.useState<string | null>(
    null
  );

  const submitAnswerMutation = useMutation({
    mutationKey: [QUERY_KEYS.CONVERSATION_SUBMIT_ANSWER],
    mutationFn: (payload: {
      sessionId: number;
      questionId: number;
      answer: "A" | "B" | "C" | "D";
    }) =>
      convoService.submitConversationTestAnswer(payload.sessionId, {
        question_id: payload.questionId,
        selected_answer: payload.answer,
      }),
    onSuccess: (data) => {
      console.log("API Response for submitAnswer:", data);
      const isCorrect = data?.user_answer_details?.is_correct;
      addMessage({ type: "feedback", content: data, sender: "ai" });
      setCurrentTestQuestion(null);
      toast.success(isCorrect ? t("api.testCorrect") : t("api.testIncorrect"));
    },
    onError: (error) => {
      toast.error(t("api.sendMessageError"), {
        description: getApiErrorMessage(error, t("api.sendMessageError")),
      });
      setSelectedOption(null);
    },
  });

  const handleAnswerSubmit = (optionKey: "A" | "B" | "C" | "D") => {
    if (!sessionId || !question?.id) return;
    setSelectedOption(optionKey);
    submitAnswerMutation.mutate({
      sessionId,
      questionId: question.id,
      answer: optionKey,
    });
  };

  // --- FIX [Part 1]: Guard Clause against missing or malformed question object ---
  if (!question || !question.options) {
    console.error("QuestionCard received incomplete data:", {
      question,
      testResult,
    });
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Question Loading Error</AlertTitle>
        <AlertDescription>
          The question data could not be displayed correctly. Please try asking
          again or contact support.
        </AlertDescription>
      </Alert>
    );
  }

  const isPending =
    submitAnswerMutation.isPending &&
    submitAnswerMutation.variables?.answer === selectedOption;
  const userAnswer = testResult?.user_answer_details?.selected_choice;
  const correctAnswer = testResult?.question?.correct_answer;

  return (
    <div className="space-y-4">
      <p className="text-lg font-semibold">{question.question_text}</p>
      <Separator />
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {/* This line is now safe because of the guard clause above */}
        {Object.entries(question.options).map(([key, value]) => {
          const optionKey = key as "A" | "B" | "C" | "D";
          const isSelected = isTestMode
            ? selectedOption === optionKey
            : userAnswer === optionKey;
          const isCorrect = !isTestMode && correctAnswer === optionKey;

          return (
            <Button
              key={key}
              variant="outline"
              size="lg"
              className={cn(
                "h-auto justify-start text-start whitespace-normal disabled:opacity-100",
                isTestMode && "hover:bg-accent hover:text-accent-foreground",
                !isTestMode &&
                  isCorrect &&
                  "bg-green-100 border-green-500 dark:bg-green-900/50 text-green-700 dark:text-green-300",
                !isTestMode &&
                  isSelected &&
                  !isCorrect &&
                  "bg-red-100 border-red-500 dark:bg-red-900/50 text-red-700 dark:text-red-300"
              )}
              onClick={() => isTestMode && handleAnswerSubmit(optionKey)}
              disabled={!isTestMode || submitAnswerMutation.isPending}
            >
              {isPending && isSelected ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <span className="mr-2 flex h-6 w-6 items-center justify-center rounded-full border rtl:ml-2">
                  {key}
                </span>
              )}
              {value}
            </Button>
          );
        })}
      </div>
      {!isTestMode && testResult && (
        <div className="mt-4 rounded-md border bg-muted p-4">
          <h4 className="mb-2 font-bold">Explanation</h4>
          <p className="text-muted-foreground">
            {testResult.question?.explanation || "No explanation provided."}
          </p>
        </div>
      )}
    </div>
  );
}
