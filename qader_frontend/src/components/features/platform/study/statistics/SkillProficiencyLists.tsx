"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { TrendingDown, TrendingUp } from "lucide-react";
import { useTranslations } from "next-intl";
import type { UserStatistics } from "@/types/api/study.types";

interface Props {
  skills: UserStatistics["skill_proficiency_summary"];
}

type Skill = UserStatistics["skill_proficiency_summary"][0];

const SkillListItem = ({
  skill,
  icon: Icon,
}: {
  skill: Skill;
  icon: React.ElementType;
}) => {
  const accuracy = skill.accuracy ?? 0;
  return (
    <div className="flex items-center gap-4 py-2">
      <Icon className="h-5 w-5 flex-shrink-0 text-muted-foreground" />
      <div className="w-full space-y-1">
        <div className="flex items-baseline justify-between">
          <p className="truncate text-sm font-medium leading-none">
            {skill.skill_name}
          </p>
          <p className="text-sm font-bold">{accuracy.toFixed(1)}%</p>
        </div>
        <Progress value={accuracy} className="h-1.5" />
      </div>
    </div>
  );
};

export function SkillProficiencyLists({ skills }: Props) {
  const t = useTranslations("Study.statistics.skillProficiency");

  const sortedByProficiency = [...skills].sort(
    (a, b) => b.proficiency_score - a.proficiency_score
  );

  const strongestSkills = sortedByProficiency.slice(0, 5);
  const weakestSkills = sortedByProficiency.slice(-5).reverse();

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="strongest" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="strongest">{t("strongest")}</TabsTrigger>
            <TabsTrigger value="weakest">{t("weakest")}</TabsTrigger>
          </TabsList>
          <TabsContent value="strongest" className="space-y-2 pt-2">
            {strongestSkills.map((skill) => (
              <SkillListItem
                key={skill.skill_slug}
                skill={skill}
                icon={TrendingUp}
              />
            ))}
          </TabsContent>
          <TabsContent value="weakest" className="space-y-2 pt-2">
            {weakestSkills.map((skill) => (
              <SkillListItem
                key={skill.skill_slug}
                skill={skill}
                icon={TrendingDown}
              />
            ))}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
