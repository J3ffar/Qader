"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import { 
  AlertCircle, 
  HelpCircle, 
  MessageSquareWarning,
  Lightbulb,
  FileQuestion,
  XCircle 
} from "lucide-react";

import { useEmergencyModeStore } from "@/store/emergency.store";
import {
  getEmergencyQuestions,
  updateEmergencySession,
  completeEmergencySession,
  getHintForQuestion,
  revealExplanationForQuestion,
  recordEliminationForQuestion,
} from "@/services/study.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { queryKeys } from "@/constants/queryKeys";

import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import { QuestionDisplayEmergency } from "./QuestionDisplayEmergency";
import { SessionPlanDetails } from "./SessionPlanDetails";
import ReportProblemForm from "./ReportProblemForm";
import { UnifiedQuestion } from "@/types/api/study.types";

// Practice Controls Component for Emergency Mode
interface PracticeControlsEmergencyProps {
  sessionId: number;
  question: UnifiedQuestion;
  isAnswered?: boolean;
}

const PracticeControlsEmergency: React.FC<PracticeControlsEmergencyProps> = ({
  sessionId,
  question,
  isAnswered = false,
}) => {
  const [revealedHint, setRevealedHint] = useState(false);
  const [revealedSolution, setRevealedSolution] = useState(false);
  const [eliminatedOptions, setEliminatedOptions] = useState<string[]>([]);

  // Reset states when question changes
  useEffect(() => {
    setRevealedHint(false);
    setRevealedSolution(false);
    setEliminatedOptions([]);
  }, [question.id]);

  // Hint mutation
  const hintMutation = useMutation({
    mutationFn: () => getHintForQuestion(sessionId.toString(), question.id),
    onSuccess: (data) => {
      if (data.hint) {
        setRevealedHint(true);
        toast.info("تم عرض التلميح");
      } else {
        toast.info("لا يوجد تلميح متاح لهذا السؤال");
      }
    },
    onError: (err) => toast.error(getApiErrorMessage(err, "خطأ في عرض التلميح")),
  });

  // Solution mutation
  const solutionMutation = useMutation({
    mutationFn: () => revealExplanationForQuestion(sessionId.toString(), question.id),
    onSuccess: () => {
      setRevealedSolution(true);
      toast.success("تم عرض طريقة الحل والإجابة الصحيحة");
    },
    onError: (err) => toast.error(getApiErrorMessage(err, "خطأ في عرض الحل")),
  });

  // Elimination mutation
  const eliminateMutation = useMutation({
    mutationFn: () => recordEliminationForQuestion(sessionId.toString(), question.id),
    onSuccess: () => {
      const options = ["A", "B", "C", "D"];
      const availableToEliminate = options.filter(
        (opt) => opt !== question.correct_answer && !eliminatedOptions.includes(opt)
      );

      if (availableToEliminate.length > 0) {
        const randomIndex = Math.floor(Math.random() * availableToEliminate.length);
        const optionToEliminate = availableToEliminate[randomIndex];
        setEliminatedOptions([...eliminatedOptions, optionToEliminate]);
        toast.success("تم حذف إجابة خاطئة");
      } else {
        toast.info("لا توجد إجابات أخرى يمكن حذفها");
      }
    },
    onError: (err) => toast.error(getApiErrorMessage(err, "خطأ في حذف الإجابة")),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>أدوات المساعدة</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col space-y-3">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => hintMutation.mutate()}
                disabled={hintMutation.isPending || revealedHint}
              >
                <Lightbulb className="me-3 h-5 w-5 text-yellow-500" />
                الحصول على تلميح
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{revealedHint ? "تم عرض التلميح" : "اضغط للحصول على تلميح"}</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => solutionMutation.mutate()}
                disabled={solutionMutation.isPending || revealedSolution}
              >
                <FileQuestion className="me-3 h-5 w-5 text-green-500" />
                عرض طريقة الحل و الكشف عن الإجابة الصحيحة
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {revealedSolution
                  ? "تم عرض الحل والإجابة"
                  : "اضغط لعرض طريقة الحل والإجابة الصحيحة"}
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
                  eliminatedOptions.length >= 2
                }
              >
                <XCircle className="me-3 h-5 w-5 text-orange-500" />
                حذف إجابة خاطئة
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {eliminatedOptions.length >= 2
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

export function EmergencyModeSessionView() {
  const t = useTranslations("Study.emergencyMode.session");
  const tResults = useTranslations("Study.emergencyMode.results");
  const {
    sessionId,
    suggestedPlan,
    questions,
    currentQuestionIndex,
    isCalmModeActive,
    setQuestions,
    setCalmMode,
    setCompleting,
    completeSession,
    endSession,
  } = useEmergencyModeStore();

  const {
    data: fetchedQuestions,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: queryKeys.emergencyMode.questions(sessionId!),
    queryFn: () => getEmergencyQuestions(sessionId!),
    enabled: !!sessionId && questions.length === 0,
    staleTime: Infinity,
  });

  const { mutate: updateSettings } = useMutation({
    mutationFn: (payload: { calm_mode_active: boolean }) =>
      updateEmergencySession({ sessionId: sessionId!, payload }),
    onSuccess: (data) => {
      toast.success(t("settingsUpdatedToast"));
      setCalmMode(data.calm_mode_active);
    },
    onError: (err) =>
      toast.error(getApiErrorMessage(err, t("settingsUpdateErrorToast"))),
  });

  const { mutate: finalizeSession } = useMutation({
    mutationKey: queryKeys.emergencyMode.complete(sessionId!),
    mutationFn: () => completeEmergencySession(sessionId!),
    onSuccess: (data) => {
      toast.success(tResults("successToast"));
      completeSession(data);
    },
    onError: (err) => {
      toast.error(tResults("errorToast"), {
        description: getApiErrorMessage(err, "حدث خطا في انهاء الجلسة!"),
      });
      endSession();
    },
  });

  const handleSessionCompletion = () => {
    setCompleting();
    finalizeSession();
  };

  useEffect(() => {
    if (fetchedQuestions) {
      setQuestions(fetchedQuestions);
    }
  }, [fetchedQuestions, setQuestions]);

  const handleCalmModeToggle = (checked: boolean) => {
    setCalmMode(checked);
    updateSettings({ calm_mode_active: checked });
  };

  const currentQuestion = useMemo(
    () => questions[currentQuestionIndex] || null,
    [questions, currentQuestionIndex]
  );
  const isLastQuestion =
    currentQuestionIndex === questions.length - 1 && questions.length > 0;

  if (!sessionId || !suggestedPlan) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>{t("sessionErrorTitle")}</AlertTitle>
        <AlertDescription>
          {t("noActiveSessionError")}
          <Button
            variant="link"
            onClick={endSession}
            className="p-0 h-auto rtl:mr-1 ltr:ml-1"
          >
            {t("startNewOneLink")}
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoading) return <SessionLoadingSkeleton />;
  if (isError)
    return (
      <Alert variant="destructive">
        {getApiErrorMessage(error, t("settingsUpdateErrorToast"))}
      </Alert>
    );

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 lg:items-start">
      {/* Main Content */}
      <div className="space-y-6 lg:col-span-2">
        {/* Question Display */}
        <AnimatePresence mode="wait">
          {currentQuestion ? (
            <motion.div
              key={currentQuestion.id}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.3 }}
            >
              <QuestionDisplayEmergency
                question={currentQuestion}
                currentQuestionNumber={currentQuestionIndex + 1}
                totalQuestions={questions.length}
                isLastQuestion={isLastQuestion}
                onLastAnswered={handleSessionCompletion}
              />
            </motion.div>
          ) : (
            <Skeleton className="h-[400px] w-full" />
          )}
        </AnimatePresence>

        {/* Practice Controls - NEW */}
        {currentQuestion && (
          <PracticeControlsEmergency
            sessionId={sessionId}
            question={currentQuestion}
            isAnswered={false}
          />
        )}

        {/* Controls and Report Problem */}
        <div className="space-y-4">
          <Card>
            <CardContent className="p-4 flex items-center justify-between">
              <Label
                htmlFor="calm-mode"
                className="flex items-center gap-2 cursor-pointer font-semibold"
              >
                <HelpCircle className="h-5 w-5 text-muted-foreground" />
                {t("calmModeLabel")}
              </Label>
              <Switch
                id="calm-mode"
                checked={isCalmModeActive}
                onCheckedChange={handleCalmModeToggle}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquareWarning className="h-5 w-5 text-muted-foreground" />
                {t("requestSupport.title")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ReportProblemForm sessionId={sessionId} />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Sidebar */}
      <div className="lg:sticky lg:top-24">
        <SessionPlanDetails plan={suggestedPlan} />
      </div>
    </div>
  );
}

// SessionLoadingSkeleton remains the same
const SessionLoadingSkeleton = () => (
  <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 lg:items-start">
    <div className="space-y-6 lg:col-span-2">
      <Skeleton className="h-[400px] w-full" />
      <Skeleton className="h-[200px] w-full" />
      <Skeleton className="h-[100px] w-full" />
      <Skeleton className="h-[250px] w-full" />
    </div>
    <div className="space-y-6">
      <Skeleton className="h-[200px] w-full" />
      <Skeleton className="h-[150px] w-full" />
      <Skeleton className="h-[180px] w-full" />
    </div>
  </div>
);
