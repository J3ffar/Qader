"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Lightbulb, FileQuestion, XCircle } from "lucide-react";

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
        toast.info("تم عرض التلميح");
      } else {
        toast.info("لا يوجد تلميح متاح لهذا السؤال");
      }
    },
    onError: (err) => toast.error(getApiErrorMessage(err, "خطأ في عرض التلميح")),
  });

  // UPDATED: Combined mutation for explanation and answer reveal
  const explanationAndAnswerMutation = useMutation({
    mutationFn: async () => {
      // First get the explanation
      const explanationData = await revealExplanationForQuestion(attemptId, questionId);
      // Then reveal the answer
      const answerData = await revealCorrectAnswerForQuestion(attemptId, questionId);
      return { explanation: explanationData.explanation, correctAnswer: answerData.correct_answer };
    },
    onSuccess: (data) => {
      // Update both explanation and revealed answer in state
      updateQuestionState({ 
        revealedExplanation: data.explanation || "",
        revealedAnswer: data.correctAnswer 
      });
      toast.success("تم عرض طريقة الحل والإجابة الصحيحة");
    },
    onError: (err) =>
      toast.error(getApiErrorMessage(err, "خطأ في عرض الحل")),
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
        toast.success("تم حذف إجابة خاطئة");
      } else {
        toast.info("لا توجد إجابات أخرى يمكن حذفها");
      }
    },
    onError: (err) =>
      toast.error(getApiErrorMessage(err, "خطأ في حذف الإجابة")),
  });

  // --- Render Logic ---

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("controls.title")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col space-y-3">
        <TooltipProvider>
          {/* Button 1: Get Hint */}
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
                <Lightbulb className="me-3 h-5 w-5 text-yellow-500" />
                الحصول على تلميح
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {questionState?.revealedHint
                  ? questionState.revealedHint
                  : "اضغط للحصول على تلميح"}
              </p>
            </TooltipContent>
          </Tooltip>

          {/* Button 2: Combined - Show Solution Method and Reveal Correct Answer */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => explanationAndAnswerMutation.mutate()}
                disabled={
                  explanationAndAnswerMutation.isPending ||
                  (!!questionState?.revealedExplanation && !!questionState?.revealedAnswer)
                }
              >
                <FileQuestion className="me-3 h-5 w-5 text-green-500" />
                عرض طريقة الحل و الكشف عن الإجابة الصحيحة
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {(questionState?.revealedExplanation && questionState?.revealedAnswer)
                  ? "تم عرض الحل والإجابة"
                  : "اضغط لعرض طريقة الحل والإجابة الصحيحة"}
              </p>
            </TooltipContent>
          </Tooltip>

          {/* Button 3: Eliminate Answer */}
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
                <XCircle className="me-3 h-5 w-5 text-orange-500" />
                حذف إجابة خاطئة
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {questionState?.eliminatedOptions && questionState.eliminatedOptions.length >= 2
                  ? "تم استخدام الحد الأقصى من الحذف"
                  : "اضغط لحذف إجابة خاطئة واحدة"}
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </CardContent>
    </Card>
  );
};
