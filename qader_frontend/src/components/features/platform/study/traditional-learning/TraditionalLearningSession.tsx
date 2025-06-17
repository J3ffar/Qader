"use client";

import React, { useState, useMemo, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Send,
  XCircle,
} from "lucide-react";

import {
  getTestAttemptDetails,
  completeTestAttempt,
  submitAnswer,
} from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import type {
  UnifiedQuestion,
  UserTestAttemptCompletionResponse,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";
import { QuestionDisplay } from "./QuestionDisplay";
import { PracticeControls } from "./PracticeControls";
import { AnswerFeedbackDialog, FeedbackData } from "./AnswerFeedbackDialog";
import { SessionStats } from "./SessionStats"; // NEW
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type OptionKey = "A" | "B" | "C" | "D";
export interface QuestionState {
  status: "unanswered" | "correct" | "incorrect";
  selectedAnswer: OptionKey | null;
  revealedAnswer?: OptionKey;
  revealedExplanation?: string;
  revealedHint?: string;
  usedElimination?: boolean;
  eliminatedOptions?: OptionKey[];
}

export default function TraditionalLearningSession({
  attemptId,
}: {
  attemptId: string;
}) {
  const t = useTranslations("Study.traditionalLearning.session");
  const commonT = useTranslations("Common");
  const router = useRouter();
  const queryClient = useQueryClient();

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [questionStates, setQuestionStates] = useState<
    Record<number, QuestionState>
  >({});
  // NEW: State for session-wide statistics
  const [sessionStats, setSessionStats] = useState({
    correct: 0,
    incorrect: 0,
  });
  const [direction, setDirection] = useState<"ltr" | "rtl">("ltr");
  const [feedbackData, setFeedbackData] = useState<FeedbackData | null>(null);

  useEffect(() => {
    setDirection(document.documentElement.dir as "ltr" | "rtl");
  }, []);

  const { data: attemptDetails, error } = useQuery({
    queryKey: [QUERY_KEYS.USER_TEST_ATTEMPT_DETAIL, attemptId],
    queryFn: () => getTestAttemptDetails(attemptId),
    refetchOnWindowFocus: false,
  });

  const questions: UnifiedQuestion[] = useMemo(
    () => attemptDetails?.included_questions || [],
    [attemptDetails]
  );
  const currentQuestion = questions[currentQuestionIndex];
  const currentQuestionState = currentQuestion
    ? questionStates[currentQuestion.id]
    : undefined;

  const submitAnswerMutation = useMutation({
    mutationFn: (payload: { questionId: number; selectedAnswer: OptionKey }) =>
      submitAnswer(attemptId, {
        question_id: payload.questionId,
        selected_answer: payload.selectedAnswer,
      }),
    onSuccess: (data, variables) => {
      const apiQuestion = data.question;
      const isCorrect = apiQuestion.user_answer_details?.is_correct ?? false;
      const correctAnswerKey = apiQuestion.correct_answer;

      setQuestionStates((prev) => ({
        ...prev,
        [variables.questionId]: {
          ...prev[variables.questionId],
          status: isCorrect ? "correct" : "incorrect",
        },
      }));

      // NEW: Update session stats
      setSessionStats((prev) => ({
        ...prev,
        correct: isCorrect ? prev.correct + 1 : prev.correct,
        incorrect: !isCorrect ? prev.incorrect + 1 : prev.incorrect,
      }));

      setFeedbackData({
        isCorrect,
        correctAnswerText: apiQuestion.options[correctAnswerKey],
        explanation: apiQuestion.explanation,
      });
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, commonT("errors.generic")));
    },
  });

  const completeSessionMutation = useMutation<
    UserTestAttemptCompletionResponse,
    Error,
    string
  >({
    mutationFn: completeTestAttempt,
    onSuccess: (data, completedAttemptId) => {
      toast.success(t("api.sessionCompletedSuccess"));

      // Invalidate the list view so it shows the 'completed' status
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.USER_TEST_ATTEMPTS],
      });

      // Cache the detailed completion result for the score page
      queryClient.setQueryData(
        [QUERY_KEYS.USER_TEST_ATTEMPT_COMPLETION_RESULT, completedAttemptId],
        data
      );

      // Redirect to the new score page
      router.push(PATHS.STUDY.TRADITIONAL_LEARNING.SCORE(completedAttemptId));
    },
    onError: (err) => {
      const errorMessage = getApiErrorMessage(
        err,
        t("api.sessionCompleteError")
      );
      toast.error(errorMessage);
    },
  });

  const handleSelectAnswer = (
    questionId: number,
    selectedAnswer: OptionKey
  ) => {
    const currentState = questionStates[questionId]?.status;
    if (currentState === "correct" || currentState === "incorrect") return;
    setQuestionStates((prev) => ({
      ...prev,
      [questionId]: {
        ...(prev[questionId] || { status: "unanswered", selectedAnswer: null }),
        selectedAnswer,
      },
    }));
    submitAnswerMutation.mutate({ questionId, selectedAnswer });
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1);
    }
  };
  const handleFeedbackDialogClose = () => {
    setFeedbackData(null);
  };

  if (error) {
    return (
      <div className="container p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-5 w-5" />
          <AlertTitle>{commonT("errors.fetchFailedTitle")}</AlertTitle>
          <AlertDescription>
            {getApiErrorMessage(error, commonT("errors.tryAgain"))}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <>
      <div className="container mx-auto max-w-7xl p-4 md:p-6">
        <header className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">{t("title")}</h1>
          <ConfirmationDialog
            triggerButton={
              <Button variant="outline" size="sm">
                <XCircle className="me-2 h-4 w-4" />
                {t("endSession")}
              </Button>
            }
            title={t("confirmEndTitle")}
            description={t("confirmEndDescription")}
            confirmActionText={t("confirmEndButton")}
            onConfirm={() => completeSessionMutation.mutate(attemptId)}
            isConfirming={completeSessionMutation.isPending}
          />
        </header>

        <Progress
          value={
            questions.length > 0
              ? ((currentQuestionIndex + 1) / questions.length) * 100
              : 0
          }
          className="mx-auto mb-6 h-2 max-w-3xl"
        />

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <main className="space-y-6 lg:col-span-2">
            {currentQuestion ? (
              <>
                <QuestionDisplay
                  key={currentQuestion.id}
                  question={currentQuestion}
                  questionState={currentQuestionState}
                  onSelectAnswer={(answer) =>
                    handleSelectAnswer(currentQuestion.id, answer)
                  }
                  direction={direction}
                />
                <div className="flex items-center justify-between">
                  <Button
                    variant="outline"
                    onClick={handlePrevious}
                    disabled={currentQuestionIndex === 0}
                  >
                    {direction === "rtl" ? (
                      <ArrowRight className="me-2 h-4 w-4" />
                    ) : (
                      <ArrowLeft className="me-2 h-4 w-4" />
                    )}
                    {t("previous")}
                  </Button>

                  {currentQuestionIndex < questions.length - 1 ? (
                    <Button onClick={handleNext}>
                      {t("next")}
                      {direction === "rtl" ? (
                        <ArrowLeft className="ms-2 h-4 w-4" />
                      ) : (
                        <ArrowRight className="ms-2 h-4 w-4" />
                      )}
                    </Button>
                  ) : (
                    <Button
                      onClick={() => completeSessionMutation.mutate(attemptId)}
                      disabled={completeSessionMutation.isPending}
                    >
                      <Send className="me-2 h-4 w-4" />
                      {t("completeSession")}
                    </Button>
                  )}
                </div>
              </>
            ) : (
              <div className="rounded-lg border p-8 text-center">
                <p>{t("noMoreQuestions")}</p>
                <Button
                  className="mt-4"
                  onClick={() => completeSessionMutation.mutate(attemptId)}
                >
                  {t("completeSession")}
                </Button>
              </div>
            )}
          </main>
          <aside className="space-y-6 lg:col-span-1">
            {/* NEW: Display session stats */}
            <SessionStats
              correct={sessionStats.correct}
              incorrect={sessionStats.incorrect}
            />
            {currentQuestion && (
              <>
                <PracticeControls
                  attemptId={attemptId}
                  question={currentQuestion} // Pass the full question object
                  questionState={currentQuestionState}
                  setQuestionStates={setQuestionStates}
                />
                <Card>
                  <CardHeader>
                    <CardTitle>{t("questionDetails")}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <p>
                      <strong>{t("section")}:</strong>{" "}
                      {currentQuestion.section.name}
                    </p>
                    <p>
                      <strong>{t("subsection")}:</strong>{" "}
                      {currentQuestion.subsection.name}
                    </p>
                    {currentQuestion.skill && (
                      <p>
                        <strong>{t("skill")}:</strong>{" "}
                        {currentQuestion.skill.name}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </aside>
        </div>
      </div>
      <AnswerFeedbackDialog
        isOpen={!!feedbackData}
        feedback={feedbackData}
        onClose={handleFeedbackDialogClose}
      />
    </>
  );
}
