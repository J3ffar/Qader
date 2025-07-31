"use client";

import React, { useEffect, useMemo } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import { AlertCircle, HelpCircle, MessageSquareWarning } from "lucide-react";

import { useEmergencyModeStore } from "@/store/emergency.store";
import {
  getEmergencyQuestions,
  updateEmergencySession,
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

import { QuestionDisplayEmergency } from "./QuestionDisplayEmergency";
import { SessionPlanDetails } from "./SessionPlanDetails";
import ReportProblemForm from "./ReportProblemForm";

export function EmergencyModeSessionView() {
  const t = useTranslations("Study.emergencyMode.session");
  const {
    sessionId,
    suggestedPlan,
    questions,
    currentQuestionIndex,
    isCalmModeActive,
    setQuestions,
    setCalmMode,
    setCompleting,
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

  useEffect(() => {
    if (fetchedQuestions) {
      setQuestions(fetchedQuestions);
    }
  }, [fetchedQuestions, setQuestions]);

  const handleCalmModeToggle = (checked: boolean) => {
    setCalmMode(checked); // Optimistic UI update
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
      {/* Main Content - REORDERED */}
      <div className="space-y-6 lg:col-span-2">
        {/* Question Display is now on top */}
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
                onLastAnswered={setCompleting}
              />
            </motion.div>
          ) : (
            // Skeleton for question if needed while other data loads
            <Skeleton className="h-[400px] w-full" />
          )}
        </AnimatePresence>

        {/* Controls are now below the question */}
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
              {/* <CardDescription>
                {t("requestSupport.description")}
              </CardDescription> */}
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
