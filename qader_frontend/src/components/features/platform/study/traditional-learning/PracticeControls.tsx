import React from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Lightbulb, Eye, FileQuestion, XCircle } from "lucide-react"; // XCircle can be used for eliminate

import {
  getHintForQuestion,
  revealCorrectAnswerForQuestion,
  revealExplanationForQuestion,
  recordEliminationForQuestion,
} from "@/services/study.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Using same QuestionState type from parent (updated to include `usedElimination`)
type OptionKey = "A" | "B" | "C" | "D";
interface QuestionState {
  status: "unanswered" | "correct" | "incorrect";
  selectedAnswer: OptionKey | null;
  revealedAnswer?: OptionKey;
  revealedExplanation?: string;
  revealedHint?: string;
  usedElimination?: boolean; // Added for tracking elimination usage
}
interface Props {
  attemptId: string;
  questionId: number;
  questionState?: QuestionState;
  setQuestionStates: React.Dispatch<
    React.SetStateAction<Record<number, QuestionState>>
  >;
}

export const PracticeControls: React.FC<Props> = ({
  attemptId,
  questionId,
  questionState,
  setQuestionStates,
}) => {
  const t = useTranslations("traditionalLearning.session");

  // Refined update function:
  // It now safely updates specific 'revealed' or 'used' properties
  const updateQuestionState = (
    keyToUpdate:
      | "revealedHint"
      | "revealedAnswer"
      | "revealedExplanation"
      | "usedElimination",
    value: any
  ) => {
    setQuestionStates((prev) => ({
      ...prev, // Keep all other questions as they are
      [questionId]: {
        // First, spread the *existing* state of the current question.
        // If it doesn't exist yet (first interaction), provide defaults.
        ...(prev[questionId] || { status: "unanswered", selectedAnswer: null }),
        // Then, apply the specific update. This will correctly override if the key already exists,
        // or add it if it's new.
        [keyToUpdate]: value,
      },
    }));
  };

  const hintMutation = useMutation({
    mutationFn: () => getHintForQuestion(attemptId, questionId),
    onSuccess: (data) => {
      if (data.hint) {
        updateQuestionState("revealedHint", data.hint);
        toast.success(t("api.hintSuccess"), { description: data.hint });
      } else {
        toast.info(t("api.hintNotAvailable"));
      }
    },
    onError: (err) =>
      toast.error(
        getApiErrorMessage(err, t("api.hintError", { error: "Unknown Error" }))
      ), // Added defaultMessage
  });

  const answerMutation = useMutation({
    mutationFn: () => revealCorrectAnswerForQuestion(attemptId, questionId),
    onSuccess: (data) => {
      updateQuestionState("revealedAnswer", data.correct_answer);
      toast.success(t("api.answerRevealSuccess"));
    },
    onError: (err) =>
      toast.error(
        getApiErrorMessage(
          err,
          t("api.answerRevealError", { error: "Unknown Error" })
        )
      ), // Added defaultMessage
  });

  const explanationMutation = useMutation({
    mutationFn: () => revealExplanationForQuestion(attemptId, questionId),
    onSuccess: (data) => {
      if (data.explanation) {
        updateQuestionState("revealedExplanation", data.explanation);
        toast.success(t("api.explanationRevealSuccess"));
      } else {
        toast.info(t("api.explanationNotAvailable"));
      }
    },
    onError: (err) =>
      toast.error(
        getApiErrorMessage(
          err,
          t("api.explanationRevealError", { error: "Unknown Error" })
        )
      ), // Added defaultMessage
  });

  const eliminateMutation = useMutation({
    mutationFn: () => recordEliminationForQuestion(attemptId, questionId),
    onSuccess: () => {
      updateQuestionState("usedElimination", true); // Mark as used
      toast.success(t("api.eliminateSuccess"));
    },
    onError: (err) =>
      toast.error(
        getApiErrorMessage(
          err,
          t("api.eliminateError", { error: "Unknown Error" })
        )
      ), // Added defaultMessage
  });

  const isAnswered = questionState?.status !== "unanswered";

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("controls.title")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <TooltipProvider>
          {/* Get a Hint */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => hintMutation.mutate()}
                disabled={
                  hintMutation.isPending ||
                  isAnswered ||
                  !!questionState?.revealedHint
                }
              >
                <Lightbulb className="me-3 h-5 w-5 text-yellow-500" />{" "}
                {t("controls.hint")}
              </Button>
            </TooltipTrigger>
            {/* Display the hint in the tooltip if revealed */}
            <TooltipContent>
              <p>{questionState?.revealedHint || t("controls.hint")}</p>
            </TooltipContent>
          </Tooltip>

          {/* Eliminate an Answer */}
          {/* Using XCircle for elimination as per original design. Can be changed if needed. */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => eliminateMutation.mutate()}
                disabled={
                  eliminateMutation.isPending ||
                  isAnswered ||
                  !!questionState?.usedElimination
                }
              >
                <XCircle className="me-3 h-5 w-5 text-red-500" />{" "}
                {t("controls.eliminate")}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{t("controls.eliminate")}</p>
            </TooltipContent>
          </Tooltip>

          {/* Reveal Correct Answer */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => answerMutation.mutate()}
                disabled={
                  answerMutation.isPending ||
                  isAnswered ||
                  !!questionState?.revealedAnswer
                }
              >
                <Eye className="me-3 h-5 w-5 text-blue-500" />{" "}
                {t("controls.showAnswer")}
              </Button>
            </TooltipTrigger>
            {/* Display the correct answer in the tooltip if revealed */}
            <TooltipContent>
              <p>
                {questionState?.revealedAnswer
                  ? `${t("correctAnswerWas")} ${questionState.revealedAnswer}`
                  : t("controls.showAnswer")}
              </p>
            </TooltipContent>
          </Tooltip>

          {/* Show Solution Method (Explanation) */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => explanationMutation.mutate()}
                disabled={
                  explanationMutation.isPending ||
                  isAnswered ||
                  !!questionState?.revealedExplanation
                }
              >
                <FileQuestion className="me-3 h-5 w-5 text-green-500" />{" "}
                {t("controls.showSolution")}
              </Button>
            </TooltipTrigger>
            {/* Display the explanation in the tooltip if revealed */}
            <TooltipContent>
              <p>
                {questionState?.revealedExplanation ||
                  t("controls.showSolution")}
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </CardContent>
    </Card>
  );
};
