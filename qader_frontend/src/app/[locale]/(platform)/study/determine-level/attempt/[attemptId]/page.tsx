"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Clock,
  XCircle,
  Loader2,
  Send,
  HelpCircle,
  Check,
  CheckCircle2,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";
import { StarButton } from "@/components/shared/StarButton";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";

import {
  resumeTestAttempt,
  submitAnswer,
  completeTestAttempt,
  cancelTestAttempt,
} from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import type {
  UserTestAttemptResume,
  UnifiedQuestion,
  SubmitAnswerPayload,
  UserTestAttemptCompletionResponse,
  SubmitAnswerResponse,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { queryKeys } from "@/constants/queryKeys";
import { QuestionRenderer } from "@/components/shared/QuestionRenderer";
import { RichContentViewer } from "@/components/shared/RichContentViewer";

type OptionKey = "A" | "B" | "C" | "D";
interface UserSelections {
  [questionId: number]: OptionKey | undefined;
}

interface ConfirmedAnswers {
  [questionId: number]: boolean;
}

const TEST_DURATION_SECONDS = 30 * 60;

// Error Report Modal Component
interface ErrorReportModalProps {
  questionId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const ErrorReportModal: React.FC<ErrorReportModalProps> = ({
  questionId,
  open,
  onOpenChange,
}) => {
  const [subject, setSubject] = useState("");
  const [problemType, setProblemType] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    
    // Here you would typically send the error report to your API
    const reportData = {
      questionId,
      subject,
      problemType,
      description,
      timestamp: new Date().toISOString(),
    };
    
    // Simulate API call
    console.log("Submitting error report:", reportData);
    
    // You would replace this with actual API call:
    // await submitErrorReport(reportData);
    
    setTimeout(() => {
      setIsSubmitting(false);
      // Reset form
      setSubject("");
      setProblemType("");
      setDescription("");
      onOpenChange(false);
      // You might want to show a success toast here
    }, 1000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]" dir="rtl">
        <DialogHeader>
          <DialogTitle>إبلاغ عن خطأ</DialogTitle>
          <DialogDescription>
            ساعدنا في تحسين المحتوى بالإبلاغ عن أي مشكلة واجهتها
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          
          <div className="grid gap-2">
            <Label htmlFor="problemType">نوع المشكلة</Label>
            <Select value={problemType} onValueChange={setProblemType}>
              <SelectTrigger id="problemType">
                <SelectValue placeholder="مشكلة في السؤال" />
              </SelectTrigger>
              <SelectContent dir="rtl">
                <SelectItem value="question_issue" defaultChecked>مشكلة في السؤال</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="description">وصف المشكلة</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="اشرح المشكلة بالتفصيل..."
              className="min-h-[100px]"
              dir="rtl"
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            إلغاء
          </Button>
          <Button
            type="submit"
            onClick={handleSubmit}
            disabled={!subject || !problemType || !description || isSubmitting}
          >
            {isSubmitting ? "جاري الإرسال..." : "إرسال"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

const LevelAssessmentAttemptPage = () => {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const t = useTranslations("Study.determineLevel.quiz");
  const tCommon = useTranslations("Common");
  const locale = params.locale as string;
  const attemptId = params.attemptId as string;

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userSelections, setUserSelections] = useState<UserSelections>({});
  const [confirmedAnswers, setConfirmedAnswers] = useState<ConfirmedAnswers>({}); // Track confirmed answers
  const [timeElapsed, setTimeElapsed] = useState(0); // Timer counts up from 00:00
  const [isTimeUp, setIsTimeUp] = useState(false);
  const [direction, setDirection] = useState<"ltr" | "rtl">("ltr");
  const [localStarred, setLocalStarred] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [questionStartTime, setQuestionStartTime] = useState<number>(0);
  const [answeredQuestions, setAnsweredQuestions] = useState<Set<number>>(new Set()); // Track answered questions
  const [isErrorModalOpen, setIsErrorModalOpen] = useState(false);

  useEffect(() => {
    setDirection(document.documentElement.dir as "ltr" | "rtl");
  }, []);

  const {
    data: attemptData,
    isLoading: isLoadingAttempt,
    error: attemptError,
    isSuccess,
  } = useQuery<UserTestAttemptResume, Error>({
    queryKey: queryKeys.tests.resume(attemptId),
    queryFn: () => resumeTestAttempt(attemptId),
    enabled: !!attemptId,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const questions: UnifiedQuestion[] = useMemo(
    () => attemptData?.questions || [],
    [attemptData]
  );

  useEffect(() => {
    if (isSuccess && attemptData) {
      if (attemptData.total_questions === attemptData.answered_question_count) {
        handleCompleteTest(false, true);
        return;
      }

      const initialSelections: UserSelections = {};
      const initialAnswered = new Set<number>();
      const initialConfirmed: ConfirmedAnswers = {};
      let firstUnansweredIndex = -1;

      attemptData.questions.forEach((q, index) => {
        if (q.user_answer_details?.selected_choice) {
          initialSelections[q.id] = q.user_answer_details.selected_choice;
          initialAnswered.add(q.id);
          initialConfirmed[q.id] = true; // Mark as confirmed if already submitted
        } else if (firstUnansweredIndex === -1) {
          firstUnansweredIndex = index;
        }
      });

      setUserSelections(initialSelections);
      setAnsweredQuestions(initialAnswered);
      setConfirmedAnswers(initialConfirmed);
      setCurrentQuestionIndex(
        firstUnansweredIndex !== -1 ? firstUnansweredIndex : 0
      );
      setIsReady(true);
    }
  }, [isSuccess, attemptData]);

  const currentQuestion: UnifiedQuestion | undefined =
    questions[currentQuestionIndex];

  useEffect(() => {
    if (isReady && currentQuestion) {
      setQuestionStartTime(Date.now());
      setLocalStarred(currentQuestion.is_starred);
    }
  }, [currentQuestionIndex, isReady, currentQuestion]);

  // Timer logic - counting UP from 00:00
  useEffect(() => {
    if (!isReady || isLoadingAttempt || isTimeUp) return;
    if (timeElapsed >= TEST_DURATION_SECONDS) {
      setIsTimeUp(true);
      toast.warning(t("timeOver"), { duration: 5000 });
      handleCompleteTest(true);
      return;
    }
    const timerId = setInterval(() => setTimeElapsed((prev) => prev + 1), 1000);
    return () => clearInterval(timerId);
  }, [timeElapsed, isLoadingAttempt, isReady, isTimeUp]);

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(secs).padStart(
      2,
      "0"
    )}`;
  };

  const submitAnswerMutation = useMutation({
    mutationFn: (payload: SubmitAnswerPayload & { attemptId: string }) =>
      submitAnswer(payload.attemptId, {
        question_id: payload.question_id,
        selected_answer: payload.selected_answer,
        time_taken_seconds: payload.time_taken_seconds,
      }),
    onSuccess: (data: SubmitAnswerResponse, variables) => {
      const queryKey = queryKeys.tests.resume(variables.attemptId);
      
      queryClient.setQueryData<UserTestAttemptResume>(queryKey, (oldData) => {
        if (!oldData) return undefined;

        const wasAlreadyAnswered =
          oldData.questions.find((q) => q.id === data.question.id)
            ?.user_answer_details !== null;

        const newQuestions = oldData.questions.map((q) =>
          q.id === data.question.id ? data.question : q
        );

        return {
          ...oldData,
          questions: newQuestions,
          answered_question_count: wasAlreadyAnswered
            ? oldData.answered_question_count
            : oldData.answered_question_count + 1,
        };
      });

      // Update answered questions set
      setAnsweredQuestions(prev => new Set([...prev, variables.question_id]));
      // Mark as confirmed
      setConfirmedAnswers(prev => ({ ...prev, [variables.question_id]: true }));
      
      toast.success(t("answerConfirmed"));
    },
    onError: (error: any, variables) => {
      const errorMsg = getApiErrorMessage(error, tCommon("errors.generic"));
      toast.error(
        t("api.answerSubmitError", {
          questionId: variables.question_id,
          error: errorMsg,
        })
      );
    },
  });

  const completeTestMutation = useMutation<
    UserTestAttemptCompletionResponse,
    Error,
    string
  >({
    mutationFn: completeTestAttempt,
    onSuccess: (data, attemptId) => {
      toast.success(t("api.testCompletedSuccess"));
      queryClient.setQueryData(
        queryKeys.tests.completionResult(attemptId),
        data
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.tests.lists(),
      });
      router.push(PATHS.STUDY.DETERMINE_LEVEL.SCORE(attemptId));
    },
    onError: (error: any) => {
      const errorMsg = getApiErrorMessage(error, tCommon("errors.generic"));
      toast.error(t("api.testCompleteError", { error: errorMsg }));
    },
  });

  const cancelTestMutation = useMutation({
    mutationFn: cancelTestAttempt,
    onSuccess: () => {
      toast.success(t("api.testCancelledSuccess"));
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });
      queryClient.removeQueries({
        queryKey: queryKeys.tests.detail(attemptId),
      });
      router.push(PATHS.STUDY.DETERMINE_LEVEL.LIST);
    },
    onError: (error: any) => {
      const errorMsg = getApiErrorMessage(error, tCommon("errors.generic"));
      toast.error(t("api.testCancelError", { error: errorMsg }));
    },
  });

  const handleSelectAnswer = (selectedOption: OptionKey) => {
    if (currentQuestion && !confirmedAnswers[currentQuestion.id]) {
      setUserSelections((prev) => ({
        ...prev,
        [currentQuestion.id]: selectedOption,
      }));
    }
  };

  const handleConfirmAnswer = async () => {
    if (currentQuestion && userSelections[currentQuestion.id] && !confirmedAnswers[currentQuestion.id]) {
      const timeTakenSeconds = Math.round((Date.now() - questionStartTime) / 1000);
      await submitAnswerMutation.mutateAsync({
        attemptId,
        question_id: currentQuestion.id,
        selected_answer: userSelections[currentQuestion.id]!,
        time_taken_seconds: timeTakenSeconds,
      });
    }
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

  const handleCompleteTest = async (
    autoSubmittedDueToTimeUp = false,
    forceComplete = false
  ) => {
    completeTestMutation.mutate(attemptId);
  };

  const handleCancelTest = () => {
    cancelTestMutation.mutate(attemptId);
  };

  // Calculate progress based on confirmed answers
  const confirmedCount = Object.values(confirmedAnswers).filter(Boolean).length;
  const progressValue = questions.length > 0 ? (confirmedCount / questions.length) * 100 : 0;

  // Check if current question is confirmed
  const isCurrentQuestionConfirmed = currentQuestion ? confirmedAnswers[currentQuestion.id] : false;
  const isCurrentQuestionAnswered = currentQuestion ? answeredQuestions.has(currentQuestion.id) : false;

  // RENDER LOGIC
  if (isLoadingAttempt || !isReady) return <QuizPageSkeleton />;
  if (attemptError || !attemptData) {
    return (
      <div className="container mx-auto flex min-h-[calc(100vh-200px)] flex-col items-center justify-center p-6">
        <Alert variant="destructive" className="max-w-md">
          <AlertTriangle className="h-5 w-5" />
          <AlertTitle>{tCommon("errors.fetchFailedTitle")}</AlertTitle>
          <AlertDescription>
            {getApiErrorMessage(attemptError, tCommon("errors.generic"))}
          </AlertDescription>
        </Alert>
        <Button
          onClick={() => router.back()}
          variant="outline"
          className="mt-6"
        >
          {locale === "ar" ? (
            <ArrowRight className="me-2 h-4 w-4" />
          ) : (
            <ArrowLeft className="me-2 h-4 w-4" />
          )}
          {tCommon("back")}
        </Button>
      </div>
    );
  }

  // غير مؤكد

  if (!currentQuestion) {
    return (
      <div className="container mx-auto flex min-h-[calc(100vh-200px)] flex-col items-center justify-center p-6">
        <Alert variant="default" className="max-w-md">
          <AlertTriangle className="h-5 w-5" />
          <AlertTitle>{t("noQuestionsTitle")}</AlertTitle>
          <AlertDescription>{t("noQuestionsDescription")}</AlertDescription>
        </Alert>
        <Button
          onClick={() => router.push(PATHS.STUDY.DETERMINE_LEVEL.LIST)}
          variant="outline"
          className="mt-6"
        >
          {locale === "ar" ? (
            <ArrowRight className="me-2 h-4 w-4" />
          ) : (
            <ArrowLeft className="me-2 h-4 w-4" />
          )}
          {tCommon("backToList")}
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto flex flex-col items-center p-4 md:p-6 lg:p-8">
      <Card className="w-full max-w-4xl shadow-xl dark:bg-[#0B1739]">
        <CardHeader dir={locale === "en" ? "ltr" : "rtl"} className="pb-4">
          <div className="mb-3 flex items-center justify-between">
            <CardTitle className="text-2xl md:text-3xl font-bold">
              {confirmedCount}/{questions.length}
            </CardTitle>
            <div className="flex items-center gap-4">
              <div className="flex items-center text-lg">
                <Clock className="me-1.5 h-5 w-5 rtl:me-0 rtl:ms-1.5" />
                <span className="font-medium">{formatTime(timeElapsed)}</span>
              </div>
              <StarButton
                questionId={currentQuestion.id}
                isStarred={localStarred}
                onStarChange={(newState) => setLocalStarred(newState)}
                disabled={false}
                attemptId={attemptId}
              />
              <ConfirmationDialog
                triggerButton={
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <XCircle className="h-4 w-4" />
                    <span className="ms-1.5 hidden sm:inline">{t("endTest")}</span>
                  </Button>
                }
                title={t("cancelDialog.title")}
                description={t("cancelDialog.description")}
                confirmActionText={t("cancelDialog.confirmButton")}
                cancelActionText={tCommon("no")}
                onConfirm={handleCancelTest}
                isConfirming={cancelTestMutation.isPending}
                confirmButtonVariant="destructive"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsErrorModalOpen(true)}
                className="flex items-center gap-2"
              >
                <AlertTriangle className="h-4 w-4" />
                <span>إبلاغ عن خطأ</span>
              </Button>
            </div>
          </div>
          <Progress value={progressValue} className="mt-2 h-2 w-full" />
        </CardHeader>

        <CardContent className="min-h-[400px] py-6">
          <div className="mb-8">
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-lg font-medium text-muted-foreground">
                {t("question")} {currentQuestionIndex + 1}
              </h3>
              <div className="flex items-center gap-2">
                {isCurrentQuestionConfirmed && (
                  <div className="flex items-center gap-1 text-green-600">
                    <CheckCircle2 className="h-4 w-4" />
                    <span className="text-sm font-medium">مؤكد</span>
                  </div>
                )}
                {userSelections[currentQuestion.id] && !isCurrentQuestionConfirmed && (
                  <div className="flex items-center gap-1 text-yellow-600">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="text-sm font-medium">غير مؤكد</span>
                  </div>
                )}
              </div>
            </div>
            <QuestionRenderer
              questionText={currentQuestion.question_text}
              imageUrl={currentQuestion.image}
            />
          </div>

          {currentQuestion.options ? (
            <>
              <RadioGroup
                value={userSelections[currentQuestion.id] || ""}
                onValueChange={(value: string) =>
                  handleSelectAnswer(value as OptionKey)
                }
                className="grid grid-cols-1 md:grid-cols-2 gap-4"
                dir={direction}
              >
                {Object.entries(currentQuestion.options).map(([key, text]) => {
                  const optionKey = key as OptionKey;
                  const isSelected = userSelections[currentQuestion.id] === optionKey;
                  
                  return (
                    <Label
                      key={optionKey}
                      htmlFor={`${currentQuestion.id}-${optionKey}`}
                      className={`
                        relative flex cursor-pointer items-center p-4 rounded-lg border-2 
                        transition-all duration-200 min-h-[80px]
                        ${isSelected 
                          ? 'border-primary bg-primary/10 shadow-md' 
                          : 'border-gray-200 dark:border-gray-700 hover:border-primary/50 hover:bg-accent'
                        }
                        ${isCurrentQuestionConfirmed ? 'opacity-80 cursor-not-allowed' : ''}
                      `}
                    >
                      <RadioGroupItem
                        value={optionKey}
                        id={`${currentQuestion.id}-${optionKey}`}
                        className="border-2 border-primary text-primary me-3 rtl:me-0 rtl:ms-3"
                        disabled={isCurrentQuestionConfirmed}
                      />
                      <div className="flex-1">
                        <RichContentViewer
                          htmlContent={text}
                          className="prose dark:prose-invert max-w-none text-base"
                        />
                      </div>
                      {isSelected && (
                        <div className="absolute top-2 end-2 rtl:end-auto rtl:start-2">
                          <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                        </div>
                      )}
                    </Label>
                  );
                })}
              </RadioGroup>
              
              {/* Confirm Answer Button */}
              {userSelections[currentQuestion.id] && !isCurrentQuestionConfirmed && (
                <div className="mt-6 flex justify-center">
                  <Button
                    onClick={handleConfirmAnswer}
                    disabled={submitAnswerMutation.isPending}
                    className="min-w-[200px]"
                    variant="default"
                  >
                    {submitAnswerMutation.isPending ? (
                      <>
                        <Loader2 className="me-2 h-4 w-4 animate-spin rtl:me-0 rtl:ms-2" />
                        {t("confirming")}
                      </>
                    ) : (
                      <>
                        <Check className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                        {t("confirmAnswer")}
                      </>
                    )}
                  </Button>
                </div>
              )}
            </>
          ) : (
            <Alert variant="destructive">
              <HelpCircle className="h-5 w-5" />
              <AlertTitle>{t("questionLoadError.title")}</AlertTitle>
              <AlertDescription>
                {t("questionLoadError.description", {
                  questionId: currentQuestion.id,
                })}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>

        <CardFooter
          dir={locale === "en" ? "ltr" : "rtl"}
          className="flex flex-col items-center justify-between gap-3 pt-6 sm:flex-row"
        >
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={
              currentQuestionIndex === 0 ||
              completeTestMutation.isPending ||
              cancelTestMutation.isPending
            }
            className="w-full sm:w-auto"
          >
            {locale === "ar" ? (
              <ChevronRight className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
            ) : (
              <ChevronLeft className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
            )}
            {t("previous")}
          </Button>
          
          {/* Question Navigation Indicator */}
          <div className="flex items-center gap-2">
            {questions.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentQuestionIndex(index)}
                className={`
                  w-2 h-2 rounded-full transition-all
                  ${index === currentQuestionIndex 
                    ? 'w-8 bg-primary' 
                    : confirmedAnswers[questions[index]?.id]
                      ? 'bg-green-500'
                      : userSelections[questions[index]?.id]
                        ? 'bg-yellow-500'
                        : 'bg-gray-300 dark:bg-gray-600'
                  }
                `}
                title={`Question ${index + 1}`}
              />
            ))}
          </div>
          
          {currentQuestionIndex < questions.length - 1 ? (
            <Button
              onClick={handleNext}
              disabled={
                completeTestMutation.isPending ||
                cancelTestMutation.isPending
              }
              className="w-full sm:w-auto"
            >
              {t("next")}
              {locale === "ar" ? (
                <ChevronLeft className="ms-2 h-5 w-5 rtl:me-2 rtl:ms-0" />
              ) : (
                <ChevronRight className="ms-2 h-5 w-5 rtl:me-2 rtl:ms-0" />
              )}
            </Button>
          ) : (
            <ConfirmationDialog
              triggerButton={
                <Button
                  className="w-full sm:w-auto"
                  disabled={
                    completeTestMutation.isPending ||
                    cancelTestMutation.isPending
                  }
                >
                  {completeTestMutation.isPending && (
                    <Loader2 className="me-2 h-4 w-4 animate-spin rtl:me-0 rtl:ms-2" />
                  )}
                  <Check className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
                  {t("submitTest")}
                </Button>
              }
              title={t("completeDialog.title")}
              description={t("completeDialog.description")}
              confirmActionText={t("completeDialog.confirmButton")}
              cancelActionText={tCommon("no")}
              onConfirm={() => handleCompleteTest(false)}
              isConfirming={completeTestMutation.isPending}
              confirmButtonVariant="default"
            />
          )}
        </CardFooter>
      </Card>

      {/* Error Report Modal */}
      <ErrorReportModal
        questionId={currentQuestion.id}
        open={isErrorModalOpen}
        onOpenChange={setIsErrorModalOpen}
      />
    </div>
  ); 
};

const QuizPageSkeleton = ({ message }: { message?: string }) => {
  return (
    <div className="container mx-auto flex flex-col items-center p-4 md:p-6 lg:p-8">
      <Card className="w-full max-w-4xl">
        <CardHeader className="pb-4">
          <div className="mb-3 flex items-center justify-between">
            <Skeleton className="h-8 w-20" />
            <div className="flex items-center gap-4">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-8 w-8" />
              <Skeleton className="h-8 w-24" />
            </div>
          </div>
          <Skeleton className="mt-2 h-2 w-full" />
        </CardHeader>
        <CardContent className="min-h-[400px] py-6">
          {message ? (
            <p className="text-center text-muted-foreground">{message}</p>
          ) : (
            <>
              <div className="mb-8">
                <Skeleton className="mb-2 h-6 w-32" />
                <Skeleton className="h-8 w-3/4" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[...Array(4)].map((_, i) => (
                  <div
                    key={i}
                    className="flex items-center p-4 rounded-lg border-2"
                  >
                    <Skeleton className="h-5 w-5 rounded-full me-3" />
                    <Skeleton className="h-6 flex-1" />
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
        <CardFooter className="flex flex-col items-center justify-between gap-3 pt-6 sm:flex-row">
          <Skeleton className="h-10 w-full sm:w-28" />
          <Skeleton className="h-10 w-full sm:w-28" />
        </CardFooter>
      </Card>
    </div>
  );
};

export default LevelAssessmentAttemptPage;
