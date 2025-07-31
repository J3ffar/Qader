"use client";

import React from "react";
import { useEmergencyModeStore } from "@/store/emergency.store";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress"; // Import ProgressProps
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Award, BrainCircuit, BarChart2 } from "lucide-react";
import { cn } from "@/lib/utils";

// Helper to determine the color class based on score
const getScoreColorClass = (score: number) => {
  if (score < 40) return "border-red-200";
  if (score < 70) return "border-yellow-200";
  return "border-green-200";
};

// NEW: A reusable component to render each performance row. This encapsulates the logic.
interface PerformanceRowProps {
  name: string;
  score: number;
  isSubsection?: boolean;
}

const PerformanceRow = ({
  name,
  score,
  isSubsection = false,
}: PerformanceRowProps) => {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-4 py-1",
        isSubsection && "py-2"
      )}
    >
      <span
        className={cn(
          "text-sm",
          isSubsection ? "text-muted-foreground" : "font-semibold"
        )}
      >
        {isSubsection && "└ "}
        {name}
      </span>
      <div className="flex items-center gap-3 w-1/2 sm:w-1/3">
        {/* FIX: Apply the color class directly to the Progress component's className prop */}
        <Progress
          value={score}
          className={cn("h-3 flex-1 border-2", getScoreColorClass(score))}
        />
        <span className="text-sm font-bold w-12 text-right">
          {score.toFixed(0)}%
        </span>
      </div>
    </div>
  );
};

export function EmergencyModeResults() {
  const t = useTranslations("Study.emergencyMode.results");
  const { sessionResults, endSession } = useEmergencyModeStore();

  if (!sessionResults) {
    return (
      <Card className="text-center p-8">
        <CardTitle>{t("noResults")}</CardTitle>
        <Button onClick={endSession} className="mt-4">
          {t("startNewButton")}
        </Button>
      </Card>
    );
  }

  const {
    overall_score,
    results_summary,
    ai_feedback,
    answered_question_count,
    correct_answers_count,
  } = sessionResults;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Overall Score Card (Unchanged) */}
      <Card>
        <CardHeader className="text-center">
          <Award className="h-12 w-12 text-primary mx-auto" />
          <CardTitle className="text-3xl font-bold">{t("title")}</CardTitle>
          <CardDescription>{t("description")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">{t("overallScore")}</p>
            <p className="text-6xl font-bold tracking-tighter">
              {overall_score.toFixed(1)}%
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              {t("correctAnswers", {
                correct: correct_answers_count,
                total: answered_question_count,
              })}
            </p>
          </div>
          <Progress
            value={overall_score}
            className={cn("w-full h-3", getScoreColorClass(overall_score))}
          />
        </CardContent>
      </Card>

      {/* AI Feedback Card (Unchanged) */}
      <Alert className="border-blue-300 dark:border-blue-800 bg-blue-50 dark:bg-blue-950">
        <BrainCircuit className="h-5 w-5 text-blue-500" />
        <AlertTitle className="text-lg font-semibold text-blue-700 dark:text-blue-400">
          {t("aiFeedbackTitle")}
        </AlertTitle>
        <AlertDescription className="mt-2 leading-relaxed">
          {ai_feedback}
        </AlertDescription>
      </Alert>

      {/* Performance Breakdown Card - Using the new PerformanceRow component */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart2 className="h-5 w-5" />
            {t("breakdownTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {Object.values(results_summary).map((section) => {
            const subsections = Object.values(section.subsections);
            return (
              <div key={section.name}>
                <PerformanceRow name={section.name} score={section.score} />

                <div className="space-y-1 rtl:pr-6 ltr:pl-6 border-l-2 rtl:border-r-2 rtl:border-l-0 border-border/40">
                  {subsections.length > 0 ? (
                    subsections.map((subsection) => (
                      <PerformanceRow
                        key={subsection.name}
                        name={subsection.name}
                        score={subsection.score}
                        isSubsection
                      />
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground py-2">
                      └ {t("noSubsections")}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      <Button onClick={endSession} size="lg" className="w-full text-lg">
        {t("startNewButton")}
      </Button>
    </div>
  );
}
