import React from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SuggestedPlan } from "@/types/api/study.types";
import {
  BookOpen,
  Sparkles,
  Target,
  Clock,
  Hash,
  CheckCircle,
} from "lucide-react";

interface SessionPlanDetailsProps {
  plan: SuggestedPlan;
}

export const SessionPlanDetails = ({ plan }: SessionPlanDetailsProps) => {
  const t = useTranslations("Study.emergencyMode.plan");

  return (
    <div className="space-y-6">
      {/* General Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>{t("planOverviewTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div className="flex justify-between items-center">
            <span className="flex items-center gap-2 text-muted-foreground">
              <CheckCircle className="h-4 w-4" /> {t("focusAreasTitle")}
            </span>
            <div className="flex gap-1">
              {plan.focus_area_names.map((name) => (
                <Badge key={name} variant="secondary">
                  {name}
                </Badge>
              ))}
            </div>
          </div>
          <div className="flex justify-between items-center">
            <span className="flex items-center gap-2 text-muted-foreground">
              <Clock className="h-4 w-4" /> {t("estimatedDuration")}
            </span>
            <span className="font-semibold">
              {t("minutes", { count: plan.estimated_duration_minutes })}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="flex items-center gap-2 text-muted-foreground">
              <Hash className="h-4 w-4" /> {t("recommendedQuestions")}
            </span>
            <span className="font-semibold">
              {plan.recommended_question_count}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Motivational Tips Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-400" />
            {t("tipsTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-inside list-disc space-y-2 text-sm rtl:pr-4">
            {plan.motivational_tips.map((tip, index) => (
              <li key={index}>{tip}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Review Topics Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-green-500" />
            {t("reviewTopicsTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {plan.quick_review_topics.map((topic) => (
            <div
              key={topic.slug}
              className="text-sm border-b pb-3 last:border-b-0"
            >
              <div className="flex justify-between items-start gap-2">
                <p className="font-semibold">{topic.name}</p>
                <Badge variant="outline">
                  {t("proficiencyLabel")}:{" "}
                  {Math.round(topic.current_proficiency * 100)}%
                </Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {topic.description}
              </p>
              {/* <p className="mt-2 text-xs bg-accent text-accent-foreground p-2 rounded-md">
                {topic.reason}
              </p> */}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Target Skills Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" />
            {t("targetSkillsTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {plan.target_skills.map((skill) => (
            <div key={skill.slug} className="rounded-md border p-3 text-sm">
              <div className="flex items-center justify-between gap-2">
                <div className="flex flex-col">
                  <span className="font-semibold">{skill.name}</span>
                  <Badge variant="outline" className="w-fit mt-1">
                    {skill.subsection_name}
                  </Badge>
                </div>
                <Badge variant="destructive">
                  {Math.round(skill.current_proficiency * 100)}%
                </Badge>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {skill.reason}
              </p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};
