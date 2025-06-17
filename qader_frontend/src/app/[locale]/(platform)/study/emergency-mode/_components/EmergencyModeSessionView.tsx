"use client";

import React, { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useEmergencyModeStore } from "@/store/emergency.store";
import { getEmergencyQuestions } from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Lightbulb, AlertCircle, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AnimatePresence, motion } from "framer-motion";

// Placeholder for the actual Question Display component
const QuestionDisplayEmergency = ({ question }: { question: any }) => (
  <Card>
    <CardHeader>
      <CardTitle>Question: {question.id}</CardTitle>
    </CardHeader>
    <CardContent>
      <p>{question.question_text}</p>
      {/* TODO: Implement full question display logic with options, submission, etc. */}
    </CardContent>
  </Card>
);

export function EmergencyModeSessionView() {
  const t = useTranslations("Study.emergencyMode");
  const { session, questions, currentQuestionIndex, setQuestions, endSession } =
    useEmergencyModeStore();

  const {
    data: fetchedQuestions,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: [QUERY_KEYS.EMERGENCY_QUESTIONS, session?.id],
    queryFn: () => getEmergencyQuestions(session!.id),
    enabled: !!session && questions.length === 0, // Only fetch if we have a session and no questions yet
    staleTime: Infinity, // Questions for a session are static
  });

  useEffect(() => {
    if (fetchedQuestions) {
      setQuestions(fetchedQuestions);
    }
  }, [fetchedQuestions, setQuestions]);

  const currentQuestion = useMemo(() => {
    if (questions.length > 0 && currentQuestionIndex < questions.length) {
      return questions[currentQuestionIndex];
    }
    return null;
  }, [questions, currentQuestionIndex]);

  if (isLoading && questions.length === 0) {
    return <SessionLoadingSkeleton />;
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>{t("questionFetchError")}</AlertTitle>
        <AlertDescription>
          {(error as Error)?.message || t("unknownError")}
        </AlertDescription>
      </Alert>
    );
  }

  if (!session) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Session Error</AlertTitle>
        <AlertDescription>
          No active session found. Please start a new one.
        </AlertDescription>
      </Alert>
    );
  }

  // Session completed view
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
      <div className="lg:col-span-2">
        <AnimatePresence mode="wait">
          {currentQuestion && (
            <motion.div
              key={currentQuestion.id}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.3 }}
            >
              <QuestionDisplayEmergency question={currentQuestion} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("suggestedPlanTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            <p className="mb-4 italic">{session.suggested_plan?.message}</p>
            <ul className="space-y-2">
              {session.suggested_plan?.topics.map((topic, index) => (
                <li key={index} className="flex justify-between">
                  <span>{topic.topic_name}</span>
                  <span className="font-semibold">
                    {topic.num_questions} {t("questionsSuffix")}
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-yellow-400" />
              {t("tipsTitle")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-inside list-disc space-y-2 text-sm">
              <li>{t("tip1")}</li>
              <li>{t("tip2")}</li>
              <li>{t("tip3")}</li>
            </ul>
          </CardContent>
        </Card>
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
