"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Lightbulb, Eye, FileQuestion, XCircle } from "lucide-react";

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
import { QuestionState } from "./TraditionalLearningSession";
import { UnifiedQuestion } from "@/types/api/study.types";

type OptionKey = "A" | "B" | "C" | "D";

interface Props {
  attemptId: string;
  question: UnifiedQuestion; // Now needs the full question object
  questionState?: QuestionState;
  setQuestionStates: React.Dispatch<
    React.SetStateAction<Record<number, QuestionState>>
  >;
}

export const PracticeControls: React.FC<Props> = ({
  attemptId,
  question,
  questionState,
  setQuestionStates,
}) => {
  const t = useTranslations("Study.traditionalLearning.session");
  const commonT = useTranslations("Common");
  const questionId = question.id;

  const isAnswered =
    questionState?.status === "correct" ||
    questionState?.status === "incorrect";

  const updateQuestionState = (update: Partial<QuestionState>) => {
    setQuestionStates((prev) => ({
      ...prev,
      [questionId]: {
        ...(prev[questionId] || { status: "unanswered", selectedAnswer: null }),
        ...update,
      },
    }));
  };

  // --- Mutations ---

  const hintMutation = useMutation({
    mutationFn: () => getHintForQuestion(attemptId, questionId),
    onSuccess: (data) => {
      if (data.hint) {
        updateQuestionState({ revealedHint: data.hint });
        toast.info(t("api.hintSuccess")); // Simple toast, UI will update
      } else {
        toast.info(t("api.hintNotAvailable"));
      }
    },
    onError: (err) => toast.error(getApiErrorMessage(err, t("api.hintError"))),
  });

  const explanationMutation = useMutation({
    mutationFn: () => revealExplanationForQuestion(attemptId, questionId),
    onSuccess: (data) => {
      if (data.explanation) {
        updateQuestionState({ revealedExplanation: data.explanation });
        toast.info(t("api.explanationRevealSuccess")); // Simple toast
      } else {
        toast.info(t("api.explanationNotAvailable"));
      }
    },
    onError: (err) =>
      toast.error(getApiErrorMessage(err, t("api.explanationRevealError"))),
  });

  const answerMutation = useMutation({
    mutationFn: () => revealCorrectAnswerForQuestion(attemptId, questionId),
    onSuccess: (data) => {
      updateQuestionState({ revealedAnswer: data.correct_answer });
      toast.success(t("api.answerRevealSuccess"));
    },
    onError: (err) =>
      toast.error(getApiErrorMessage(err, t("api.answerRevealError"))),
  });

  const eliminateMutation = useMutation({
    mutationFn: () => recordEliminationForQuestion(attemptId, questionId),
    onSuccess: () => {
      // NEW: Client-side logic to choose an option to eliminate
      const options = Object.keys(question.options) as OptionKey[];
      const incorrectOptions = options.filter(
        (opt) => opt !== question.correct_answer
      );

      // Find an incorrect option that hasn't already been eliminated
      const optionToEliminate = incorrectOptions.find(
        (opt) => !questionState?.eliminatedOptions?.includes(opt)
      );

      if (optionToEliminate) {
        const currentEliminated = questionState?.eliminatedOptions || [];
        updateQuestionState({
          usedElimination: true,
          eliminatedOptions: [...currentEliminated, optionToEliminate],
        });
        toast.success(t("api.eliminateSuccess"));
      }
    },
    onError: (err) =>
      toast.error(getApiErrorMessage(err, t("api.eliminateError"))),
  });

  // --- Render Logic ---

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("controls.title")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col space-y-3">
        <TooltipProvider>
          {/* --- Learning Tools (Enabled Post-Answer) --- */}

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => hintMutation.mutate()}
                // *** THE CHANGE IS HERE ***: Removed `isAnswered` check.
                disabled={
                  hintMutation.isPending || !!questionState?.revealedHint
                }
              >
                <Lightbulb className="me-3 h-5 w-5 text-yellow-500" />{" "}
                {t("controls.hint")}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {questionState?.revealedHint
                  ? questionState.revealedHint
                  : t("controls.hint")}
              </p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => explanationMutation.mutate()}
                // *** THE CHANGE IS HERE ***: Removed `isAnswered` check.
                disabled={
                  explanationMutation.isPending ||
                  !!questionState?.revealedExplanation
                }
              >
                <FileQuestion className="me-3 h-5 w-5 text-green-500" />{" "}
                {t("controls.showSolution")}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {questionState?.revealedExplanation
                  ? commonT("explanationRevealed")
                  : t("controls.showSolution")}
              </p>
            </TooltipContent>
          </Tooltip>

          {/* --- Answering Tools (Disabled Post-Answer) --- */}

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => eliminateMutation.mutate()}
                // No change here: this tool is only for before answering.
                disabled={
                  isAnswered ||
                  eliminateMutation.isPending ||
                  !!questionState?.usedElimination
                }
              >
                <XCircle className="me-3 h-5 w-5 text-orange-500" />{" "}
                {t("controls.eliminate")}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{t("controls.eliminate")}</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => answerMutation.mutate()}
                // No change here: this is redundant after the feedback dialog.
                disabled={
                  isAnswered ||
                  answerMutation.isPending ||
                  !!questionState?.revealedAnswer
                }
              >
                <Eye className="me-3 h-5 w-5 text-blue-500" />{" "}
                {t("controls.showAnswer")}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{t("controls.showAnswer")}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </CardContent>
    </Card>
  );
};

// A helper for DRY principle, but omitted for brevity in this response.
// The main logic is in the button `disabled` props above.
