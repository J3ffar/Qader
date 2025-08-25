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

// MODIFIED: Use resumeTestAttempt
import {
  resumeTestAttempt,
  completeTestAttempt,
  submitAnswer,
} from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import type {
  UnifiedQuestion,
  UserTestAttemptCompletionResponse,
  UserTestAttemptResume, // NEW
  SubmitAnswerResponse, // NEW
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";
import { QuestionDisplay } from "./QuestionDisplay";
import { PracticeControls } from "./PracticeControls";
import { AnswerFeedbackDialog, FeedbackData } from "./AnswerFeedbackDialog";
import { SessionStats } from "./SessionStats";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { queryKeys } from "@/constants/queryKeys";
import { Skeleton } from "@/components/ui/skeleton"; // Import Skeleton

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

// Define interface for extended feedback data with points
interface ExtendedFeedbackData extends FeedbackData {
  pointsEarned?: number;
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
  const [sessionStats, setSessionStats] = useState({
    correct: 0,
    incorrect: 0,
    totalPoints: 0, // NEW: Added total points tracking
  });
  const [direction, setDirection] = useState<"ltr" | "rtl">("ltr");
  const [feedbackData, setFeedbackData] = useState<ExtendedFeedbackData | null>(null);

  // NEW: State for time tracking per question
  const [questionStartTime, setQuestionStartTime] = useState<number>(0);

  useEffect(() => {
    setDirection(document.documentElement.dir as "ltr" | "rtl");
  }, []);

  // MODIFIED: Use resumeTestAttempt and handle its state here
  const {
    data: attemptData,
    isLoading,
    error,
  } = useQuery<UserTestAttemptResume, Error>({
    queryKey: queryKeys.tests.resume(attemptId),
    queryFn: () => resumeTestAttempt(attemptId),
    refetchOnWindowFocus: false,
    enabled: !!attemptId,
  });

  const questions: UnifiedQuestion[] = useMemo(
    () => attemptData?.questions || [],
    [attemptData]
  );
  const currentQuestion = questions[currentQuestionIndex];
  const currentQuestionState = currentQuestion
    ? questionStates[currentQuestion.id]
    : undefined;

  // FIXED: Updated useEffect with proper type checking for points_earned
  useEffect(() => {
    if (attemptData) {
      const initialStates: Record<number, QuestionState> = {};
      let correctCount = 0;
      let incorrectCount = 0;
      let pointsCount = 0; // NEW: Initialize points counter

      attemptData.questions.forEach((q) => {
        if (q.user_answer_details) {
          initialStates[q.id] = {
            status: q.user_answer_details.is_correct ? "correct" : "incorrect",
            selectedAnswer: q.user_answer_details.selected_choice,
            // You can extend this to include hints, explanations if they are part of resume data
          };
          
          if (q.user_answer_details.is_correct) {
            correctCount++;
            // FIX: Handle points_earned properly - check if it exists on the response
            // If points_earned doesn't exist in the API response, use default value of 10
            const pointsEarned = (q.user_answer_details as any).points_earned || 10;
            pointsCount += pointsEarned;
          } else {
            incorrectCount++;
          }
        }
      });
      
      setQuestionStates(initialStates);
      setSessionStats({ 
        correct: correctCount, 
        incorrect: incorrectCount,
        totalPoints: pointsCount // NEW: Set initial points
      });
    }
  }, [attemptData]);

  // NEW: Effect to start timer when question changes
  useEffect(() => {
    if (currentQuestion) {
      setQuestionStartTime(Date.now());
    }
  }, [currentQuestionIndex, currentQuestion]);

  // FIXED: Updated mutation with proper points tracking and type handling
  const submitAnswerMutation = useMutation({
    mutationFn: (payload: {
      questionId: number;
      selectedAnswer: OptionKey;
      timeTaken: number;
    }) =>
      submitAnswer(attemptId, {
        question_id: payload.questionId,
        selected_answer: payload.selectedAnswer,
        time_taken_seconds: payload.timeTaken,
      }),
    onSuccess: (data: SubmitAnswerResponse, variables) => {
      const apiQuestion = data.question;
      const isCorrect = apiQuestion.user_answer_details?.is_correct ?? false;
      const correctAnswerKey = apiQuestion.correct_answer;
      
      // FIX: Safely access points_earned with type assertion and default value
      const pointsEarned = isCorrect 
        ? ((apiQuestion.user_answer_details as any)?.points_earned || 10) 
        : 0;

      // Update local component state for immediate feedback
      setQuestionStates((prev) => ({
        ...prev,
        [variables.questionId]: {
          ...(prev[variables.questionId] || { selectedAnswer: null }),
          status: isCorrect ? "correct" : "incorrect",
        },
      }));

      // UPDATED: Include points in session stats
      setSessionStats((prev) => ({
        ...prev,
        correct: isCorrect ? prev.correct + 1 : prev.correct,
        incorrect: !isCorrect ? prev.incorrect + 1 : prev.incorrect,
        totalPoints: prev.totalPoints + pointsEarned, // NEW: Update total points
      }));

      setFeedbackData({
        isCorrect,
        correctAnswerText: apiQuestion.options[correctAnswerKey],
        explanation: apiQuestion.explanation,
        pointsEarned, // NEW: Include points in feedback (optional)
      });

      // Show points toast notification for correct answers
      if (isCorrect && pointsEarned > 0) {
        toast.success(`+${pointsEarned} نقاط! 🎉`);
      }

      // KEY FIX: Manually update the React Query cache
      queryClient.setQueryData<UserTestAttemptResume>(
        queryKeys.tests.resume(attemptId),
        (oldData) => {
          if (!oldData) return undefined;
          const newQuestions = oldData.questions.map((q) =>
            q.id === apiQuestion.id ? apiQuestion : q
          );
          return { ...oldData, questions: newQuestions };
        }
      );
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
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });

      // Cache the detailed completion result for the score page
      queryClient.setQueryData(
        queryKeys.tests.completionResult(completedAttemptId),
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
    const timeTaken = Math.round((Date.now() - questionStartTime) / 1000);
    submitAnswerMutation.mutate({ questionId, selectedAnswer, timeTaken });
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

  if (isLoading) return <LoadingSkeleton />; // Use a dedicated skeleton
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
                  attemptId={attemptId}
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
            {/* UPDATED: Display session stats with points */}
            <SessionStats
              correct={sessionStats.correct}
              incorrect={sessionStats.incorrect}
              totalPoints={sessionStats.totalPoints}
            />
            {currentQuestion && (
              <>
                <PracticeControls
                  attemptId={attemptId}
                  question={currentQuestion}
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

// NEW: Loading Skeleton component defined within the same file for simplicity
const LoadingSkeleton = () => {
  return (
    <div className="container mx-auto max-w-7xl animate-pulse p-4 md:p-6">
      <div className="mb-6 flex items-center justify-between">
        <Skeleton className="h-8 w-48 rounded-md" />
        <Skeleton className="h-9 w-32 rounded-md" />
      </div>

      <Skeleton className="mx-auto mb-6 h-2 max-w-3xl rounded-full" />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Main Question Area Skeleton */}
        <div className="space-y-6 lg:col-span-2">
          <Skeleton className="h-96 w-full rounded-xl" />
          <div className="flex items-center justify-between">
            <Skeleton className="h-10 w-32 rounded-md" />
            <Skeleton className="h-10 w-32 rounded-md" />
          </div>
        </div>

        {/* Sidebar Skeleton */}
        <div className="space-y-6 lg:col-span-1">
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-56 w-full rounded-xl" />
          <Skeleton className="h-40 w-full rounded-xl" />
        </div>
      </div>
    </div>
  );
};
