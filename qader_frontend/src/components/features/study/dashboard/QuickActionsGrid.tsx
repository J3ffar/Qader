import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ArrowRight,
  BookOpenText,
  BarChart3,
  Gift,
  PlayCircle,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { UserProfile } from "@/types/api/auth.types"; // Assuming UserProfile type
import { PATHS } from "@/constants/paths";
import Link from "next/link";

interface QuickActionsGridProps {
  user: UserProfile;
}

interface ActionItem {
  titleKey: string;
  descriptionKey: string;
  href: string;
  icon: React.ElementType;
  showCondition?: (user: UserProfile) => boolean;
  dynamicHref?: (user: UserProfile) => string;
  dynamicTitleKey?: (user: UserProfile) => string;
}

export const QuickActionsGrid: React.FC<QuickActionsGridProps> = ({ user }) => {
  const t = useTranslations("Study.StudyPage.dashboard.quickActions");
  const tNav = useTranslations("Nav.UserSideBar.study"); // For dynamic titles like "Traditional Learning"

  const actionItems: ActionItem[] = [
    {
      titleKey: user.last_visited_study_option
        ? "continueLearning"
        : "startTraditionalLearning",
      dynamicTitleKey: (currentUser) => {
        if (currentUser.last_visited_study_option) {
          // You might need a mapping from slug to display name here
          // For simplicity, let's assume a helper or direct translation key based on slug
          // Example: return tNav(currentUser.last_visited_study_option as any) || tNav("traditionalLearning");
          // This requires your nav.json to have keys matching study option slugs
          // Or, you'd fetch section names. For now, a generic title.
          return t("continueLearningTitle", {
            section: tNav(
              (currentUser.last_visited_study_option as any) ||
                "traditionalLearning"
            ),
          });
        }
        return t("startTraditionalLearningTitle");
      },
      descriptionKey: user.last_visited_study_option
        ? "continueLearningDescription"
        : "startTraditionalLearningDescription",
      href: user.last_visited_study_option
        ? `${PATHS.STUDY_HOME}/${user.last_visited_study_option}`
        : `${PATHS.STUDY_HOME}/traditional-learning`, // Default to traditional learning
      icon: PlayCircle,
    },
    {
      titleKey: "traditionalLearningTitle",
      descriptionKey: "traditionalLearningDescription",
      href: `${PATHS.STUDY_HOME}/traditional-learning`,
      icon: BookOpenText,
      showCondition: (currentUser) => !!currentUser.last_visited_study_option, // Show if "Continue" is different
    },
    {
      titleKey: "viewStatisticsTitle",
      descriptionKey: "viewStatisticsDescription",
      href: `${PATHS.STUDY_HOME}/statistics`,
      icon: BarChart3,
    },
    {
      titleKey: "checkRewardsTitle",
      descriptionKey: "checkRewardsDescription",
      href: `${PATHS.STUDY_HOME}/rewards-and-competitions`, // Assuming this path exists
      icon: Gift,
    },
  ];

  return (
    <div>
      <h2 className="mb-4 text-xl font-semibold">{t("title")}</h2>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {actionItems.map((item) => {
          if (item.showCondition && !item.showCondition(user)) {
            return null;
          }
          const title = item.dynamicTitleKey
            ? item.dynamicTitleKey(user)
            : t(item.titleKey);
          const href = item.dynamicHref ? item.dynamicHref(user) : item.href;

          return (
            <Link href={href} key={item.titleKey} className="group">
              <Card className="h-full transition-all group-hover:border-primary group-hover:shadow-lg">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <item.icon className="mb-2 h-8 w-8 text-primary" />
                    <ArrowRight className="h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1 group-hover:text-primary" />
                  </div>
                  <CardTitle className="text-lg">{title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    {t(item.descriptionKey)}
                  </p>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
};
