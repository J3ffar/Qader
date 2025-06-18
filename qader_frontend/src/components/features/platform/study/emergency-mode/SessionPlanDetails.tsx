import React from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SuggestedPlan } from "@/types/api/study.types";
import { BookOpen, Sparkles, Target } from "lucide-react";

interface SessionPlanDetailsProps {
  plan: SuggestedPlan;
}

export const SessionPlanDetails = ({ plan }: SessionPlanDetailsProps) => {
  const t = useTranslations("Study.emergencyMode.plan");

  return (
    <div className="space-y-6">
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
              <div className="flex items-start justify-between">
                <span className="font-semibold">{skill.name}</span>
                <Badge variant="secondary">
                  {Math.round(skill.current_proficiency * 100)}%
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">{skill.reason}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-green-500" />
            {t("reviewTopicsTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {plan.quick_review_topics.map((topic) => (
            <div key={topic.slug} className="text-sm">
              <p className="font-semibold">{topic.name}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-400" />
            {t("tipsTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-inside list-disc space-y-2 text-sm">
            {plan.motivational_tips.map((tip, index) => (
              <li key={index}>{tip}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};
