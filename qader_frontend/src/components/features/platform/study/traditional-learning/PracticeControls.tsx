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
import { QuestionState } from "./TraditionalLearningSession"; // Import the shared state type

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
  const t = useTranslations("Study.traditionalLearning.session");
  const commonT = useTranslations("Common");

  // This flag is now used ONLY for tools that should be disabled post-answer.
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

  const hintMutation = useMutation({
    mutationFn: () => getHintForQuestion(attemptId, questionId),
    onSuccess: (data) => {
      if (data.hint) {
        updateQuestionState({ revealedHint: data.hint });
        toast.info(t("api.hintSuccess"), { description: data.hint });
      } else {
        toast.info(t("api.hintNotAvailable"));
      }
    },
    onError: (err) => toast.error(getApiErrorMessage(err, t("api.hintError"))),
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

  const explanationMutation = useMutation({
    mutationFn: () => revealExplanationForQuestion(attemptId, questionId),
    onSuccess: (data) => {
      if (data.explanation) {
        updateQuestionState({ revealedExplanation: data.explanation });
        // Show explanation in a more persistent toast
        toast.info(t("api.explanationRevealSuccess"), {
          description: data.explanation,
          duration: 10000,
        });
      } else {
        toast.info(t("api.explanationNotAvailable"));
      }
    },
    onError: (err) =>
      toast.error(getApiErrorMessage(err, t("api.explanationRevealError"))),
  });

  const eliminateMutation = useMutation({
    mutationFn: () => recordEliminationForQuestion(attemptId, questionId),
    onSuccess: () => {
      updateQuestionState({ usedElimination: true });
      toast.success(t("api.eliminateSuccess"));
    },
    onError: (err) =>
      toast.error(getApiErrorMessage(err, t("api.eliminateError"))),
  });

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
