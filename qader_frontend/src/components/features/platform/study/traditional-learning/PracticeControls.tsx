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
  question: UnifiedQuestion;
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
        toast.info(t("api.hintSuccess"));
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
        toast.info(t("api.explanationRevealSuccess"));
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
      const options = Object.keys(question.options) as OptionKey[];
      const alreadyEliminated = questionState?.eliminatedOptions || [];

      // Step 1: Create a pool of options that are incorrect AND not yet eliminated.
      const availableToEliminate = options.filter(
        (opt) =>
          opt !== question.correct_answer && !alreadyEliminated.includes(opt)
      );

      // Step 2: If there's at least one option to eliminate, pick one randomly.
      if (availableToEliminate.length > 0) {
        // Step 2a: Generate a random index for the available options array.
        const randomIndex = Math.floor(
          Math.random() * availableToEliminate.length
        );
        const optionToEliminate = availableToEliminate[randomIndex];

        // Step 2b: Update the state with the randomly selected option.
        updateQuestionState({
          usedElimination: true,
          eliminatedOptions: [...alreadyEliminated, optionToEliminate],
        });
        toast.success(t("api.eliminateSuccess"));
      } else {
        // This case should ideally not be reachable if the button is disabled correctly,
        // but it's good practice to handle it.
        toast.info(t("api.noOptionsToEliminate"));
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
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => hintMutation.mutate()}
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

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => eliminateMutation.mutate()}
                disabled={
                  isAnswered ||
                  eliminateMutation.isPending ||
                  (questionState?.eliminatedOptions &&
                    questionState.eliminatedOptions.length >= 2) || // Disable after two eliminations
                  !!questionState?.usedElimination // Assuming one-time use per question
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
