"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTranslations } from "next-intl";
import type { UserStatistics } from "@/types/api/study.types";
import { SkillProficiencyLists } from "./SkillProficiencyLists";
import { RecentTestsTable } from "./RecentTestsTable";

interface Props {
  skills: UserStatistics["skill_proficiency_summary"];
  tests: UserStatistics["test_history_summary"];
}

export function ActionableInsightsTabs({ skills, tests }: Props) {
  const t = useTranslations("Study.statistics.actionableInsights");

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="skills">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="skills">{t("skillsTab")}</TabsTrigger>
            <TabsTrigger value="tests">{t("testsTab")}</TabsTrigger>
          </TabsList>
          <TabsContent value="skills" className="pt-4">
            <SkillProficiencyLists skills={skills} />
          </TabsContent>
          <TabsContent value="tests" className="pt-4">
            <RecentTestsTable tests={tests} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
