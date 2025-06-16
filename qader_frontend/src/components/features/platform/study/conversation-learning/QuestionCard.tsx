// src/components/features/platform/study/conversation-learning/QuestionCard.tsx
"use client";

import React from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useTranslations } from "next-intl";
// No longer need CheckCircleIcon, XCircleIcon as coloring is done via Tailwind classes directly
// import { CheckCircleIcon, XCircleIcon } from "@heroicons/react/24/solid";

import * as convoService from "@/services/conversation.service";
import { useConversationStore } from "@/store/conversation.store";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { cn } from "@/lib/utils"; // Tailwind CSS utility for conditional classes
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { ConversationTestResult } from "@/types/api/conversation.types"; // Correct import for ConversationTestResult

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Loader2 } from "lucide-react"; // For loading spinner
import { UnifiedQuestion } from "@/types/api/study.types";

interface QuestionCardProps {
  question: UnifiedQuestion;
  isTestMode: boolean; // Is the user currently answering this question as a test?
  testResult?: ConversationTestResult; // Populated after answering in non-test mode (i.e., for feedback/review)
}

export function QuestionCard({
  question,
  isTestMode,
  testResult,
}: QuestionCardProps) {
  const t = useTranslations("Study.conversationalLearning");
  const { sessionId, addMessage, setActiveTestQuestion } =
    useConversationStore();
  const [selectedOption, setSelectedOption] = React.useState<string | null>(
    null
  );

  // Mutation to submit the user's answer to the AI test question
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
      // Add the AI's feedback message to the chat history
      addMessage({ type: "feedback", content: data, sender: "ai" });
      // Clear the active test question in the store, as it has been answered
      setActiveTestQuestion(null);
      // Show a toast notification based on correctness
      toast.success(
        data.is_correct ? t("api.testCorrect") : t("api.testIncorrect")
      );
    },
    onError: (error) => {
      toast.error(t("api.sendMessageError"), {
        description: getApiErrorMessage(error, t("api.sendMessageError")),
      });
      // On error, allow the user to re-select an option and try again
      setSelectedOption(null);
    },
  });

  // Handler for when a user clicks on an answer option in test mode
  const handleAnswerSubmit = (optionKey: "A" | "B" | "C" | "D") => {
    if (!sessionId || submitAnswerMutation.isPending) return; // Prevent multiple submissions or if no session
    setSelectedOption(optionKey); // Visually indicate the selected option immediately
    submitAnswerMutation.mutate({
      sessionId,
      questionId: question.id,
      answer: optionKey,
    });
  };

  // Determine if a specific option button should show a loading spinner
  const isPending =
    submitAnswerMutation.isPending &&
    submitAnswerMutation.variables?.answer === selectedOption;

  // Extract user's answer and correct answer for displaying feedback/review
  // These values come directly from the `testResult` prop (which is of type ConversationTestResult)
  const userAnswer = testResult?.selected_answer;
  const correctAnswer = testResult?.question.correct_answer;

  return (
    <div className="space-y-4">
      {/* Question text */}
      <p className="text-lg font-semibold text-foreground rtl:text-right">
        {question.question_text}
      </p>
      <Separator /> {/* Visual separator */}
      {/* Answer options */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {Object.entries(question.options).map(([key, value]) => {
          const optionKey = key as "A" | "B" | "C" | "D";

          // Determine styling based on mode (test vs. feedback) and correctness
          const isSelected = isTestMode
            ? selectedOption === optionKey
            : userAnswer === optionKey;
          const isCorrectOption = !isTestMode && correctAnswer === optionKey;
          const isUserChoiceAndIncorrect =
            !isTestMode && isSelected && !isCorrectOption;

          return (
            <Button
              key={key}
              variant="outline"
              size="lg"
              className={cn(
                "h-auto justify-start text-start whitespace-normal disabled:opacity-100", // Default styles
                isTestMode && "hover:bg-accent hover:text-accent-foreground", // Hover effect in test mode
                isCorrectOption &&
                  "bg-green-100 border-green-500 text-green-700 dark:bg-green-900/50 dark:text-green-300", // Correct answer styling
                isUserChoiceAndIncorrect &&
                  "bg-red-100 border-red-500 text-red-700 dark:bg-red-900/50 dark:text-red-300" // Incorrect user choice styling
              )}
              onClick={() => isTestMode && handleAnswerSubmit(optionKey)}
              disabled={!isTestMode || submitAnswerMutation.isPending} // Disable if not in test mode or if submitting
            >
              {isPending && isSelected ? (
                // Show loader if this option is selected and submission is pending
                <Loader2 className="mr-2 h-4 w-4 animate-spin rtl:ml-2 rtl:mr-0" />
              ) : (
                // Display option letter
                <span className="mr-2 flex h-6 w-6 items-center justify-center rounded-full border rtl:ml-2 rtl:mr-0">
                  {key}
                </span>
              )}
              {value}
            </Button>
          );
        })}
      </div>
      {/* Explanation section, only visible after a test answer has been submitted (not in test mode) */}
      {!isTestMode && testResult && (
        <div className="mt-4 rounded-md border bg-muted p-4">
          <h4 className="mb-2 font-bold text-foreground rtl:text-right">
            {t("session.explanation")} {/* "Explanation" */}
          </h4>
          <p className="leading-relaxed text-muted-foreground rtl:text-right">
            {/* The explanation is now directly on `testResult.question` */}
            {testResult.question.explanation ||
              t("session.explanationNotAvailable")}
          </p>
        </div>
      )}
    </div>
  );
}
