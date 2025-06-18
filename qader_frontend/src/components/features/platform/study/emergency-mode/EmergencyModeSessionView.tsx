"use client";

import React, { useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useEmergencyModeStore } from "@/store/emergency.store";
import {
  getEmergencyQuestions,
  updateEmergencySession,
} from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { QuestionDisplayEmergency } from "./QuestionDisplayEmergency";
import { SessionPlanDetails } from "./SessionPlanDetails";

export function EmergencyModeSessionView() {
  const t = useTranslations("Study.emergencyMode.session");
  const queryClient = useQueryClient();
  const {
    sessionId,
    suggestedPlan,
    questions,
    currentQuestionIndex,
    isCalmModeActive,
    isSharedWithAdmin,
    setQuestions,
    endSession,
    setCalmMode,
    setSharedWithAdmin,
  } = useEmergencyModeStore();

  const {
    data: fetchedQuestions,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: [QUERY_KEYS.EMERGENCY_QUESTIONS, sessionId],
    queryFn: () => getEmergencyQuestions(sessionId!),
    enabled: !!sessionId && questions.length === 0,
    staleTime: Infinity,
  });

  const { mutate: updateSettings } = useMutation({
    mutationKey: [QUERY_KEYS.UPDATE_EMERGENCY_SESSION, sessionId],
    mutationFn: (payload: {
      calm_mode_active?: boolean;
      shared_with_admin?: boolean;
    }) => updateEmergencySession({ sessionId: sessionId!, payload }),
    onSuccess: (data) => {
      toast.success(t("settingsUpdatedToast"));
      // Sync local store state with the response from the server
      setCalmMode(data.calm_mode_active);
      setSharedWithAdmin(data.shared_with_admin);
    },
    onError: (error) =>
      toast.error(t("settingsUpdateErrorToast"), {
        description: getApiErrorMessage(error, t("settingsUpdateErrorToast")),
      }),
  });

  useEffect(() => {
    if (fetchedQuestions) setQuestions(fetchedQuestions);
  }, [fetchedQuestions, setQuestions]);

  const currentQuestion = useMemo(
    () => questions[currentQuestionIndex] || null,
    [questions, currentQuestionIndex]
  );

  const handleCalmModeToggle = (checked: boolean) => {
    setCalmMode(checked); // Optimistic UI update
    updateSettings({ calm_mode_active: checked });
  };

  const handleShareToggle = (checked: boolean) => {
    setSharedWithAdmin(checked); // Optimistic UI update
    updateSettings({ shared_with_admin: checked });
  };

  if (!sessionId || !suggestedPlan) {
    // This case handles returning to the page after closing the tab
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>{t("sessionErrorTitle")}</AlertTitle>
        <AlertDescription>
          {t("noActiveSessionError")}
          <Button
            variant="link"
            onClick={endSession}
            className="ml-1 h-auto p-0"
          >
            {t("startNewOneLink")}
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (isLoading && questions.length === 0) return <SessionLoadingSkeleton />;
  if (isError) return <Alert variant="destructive">...</Alert>;

  if (currentQuestionIndex >= questions.length && questions.length > 0) {
    return (
      <Card className="text-center">
        <CardHeader>
          <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
          <CardTitle>{t("sessionCompleteTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p>{t("sessionCompleteMessage")}</p>
          <Button onClick={endSession} className="mt-4">
            {t("returnToSetupButton")}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle>{t("settingsTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="calm-mode">{t("calmModeLabel")}</Label>
              <Switch
                id="calm-mode"
                checked={isCalmModeActive}
                onCheckedChange={handleCalmModeToggle}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="share-admin">{t("shareWithAdminLabel")}</Label>
              <Switch
                id="share-admin"
                checked={isSharedWithAdmin}
                onCheckedChange={handleShareToggle}
              />
            </div>
          </CardContent>
        </Card>
        <AnimatePresence mode="wait">
          {currentQuestion ? (
            <motion.div
              key={currentQuestion.id}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.3 }}
            >
              {/* THIS IS THE UPDATED PART */}
              <QuestionDisplayEmergency
                question={currentQuestion}
                currentQuestionNumber={currentQuestionIndex + 1}
                totalQuestions={questions.length}
              />
            </motion.div>
          ) : isLoading ? (
            <Skeleton className="h-96 w-full" />
          ) : null}
        </AnimatePresence>
      </div>
      <div>
        <SessionPlanDetails plan={suggestedPlan} />
      </div>
    </div>
  );
}

const SessionLoadingSkeleton = () => (
  <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
    <div className="space-y-4 lg:col-span-2">
      <Skeleton className="h-48 w-full" />
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-12 w-full" />
    </div>
    <div className="space-y-6">
      <Skeleton className="h-40 w-full" />
      <Skeleton className="h-32 w-full" />
    </div>
  </div>
);
