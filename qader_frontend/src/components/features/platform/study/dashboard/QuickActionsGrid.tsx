import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ArrowRight,
  BookOpenText,
  BarChart3,
  Gift,
  PlayCircle,
  Sparkles,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { UserProfile } from "@/types/api/auth.types";
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
  colorScheme: {
    gradient: string;
    iconColor: string;
    textColor: string;
    hoverShadow: string;
    glowColor: string;
    darkGradient: string;
    darkText: string;
  };
}

export const QuickActionsGrid: React.FC<QuickActionsGridProps> = ({ user }) => {
  const t = useTranslations("Study.StudyPage.dashboard.quickActions");
  const tNav = useTranslations("Nav.PlatformSidebar.items");

  const actionItems: ActionItem[] = [
    {
      titleKey: user.last_visited_study_option
        ? "continueLearning"
        : "startTraditionalLearning",
      dynamicTitleKey: (currentUser) => {
        if (currentUser.last_visited_study_option) {
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
        ? `${PATHS.STUDY.HOME}/${user.last_visited_study_option}`
        : `${PATHS.STUDY.HOME}/traditional-learning`,
      icon: PlayCircle,
      colorScheme: {
        gradient: "from-blue-50 via-indigo-50 to-blue-100",
        iconColor: "text-[#074182]",
        textColor: "text-[#074182]",
        hoverShadow: "hover:shadow-blue-500/25",
        glowColor: "from-blue-400 to-indigo-500",
        darkGradient: "dark:from-blue-950/20 dark:via-indigo-950/20 dark:to-blue-900/20",
        darkText: "dark:text-blue-200",
      },
    },
    {
      titleKey: "traditionalLearningTitle",
      descriptionKey: "traditionalLearningDescription",
      href: `${PATHS.STUDY.HOME}/traditional-learning`,
      icon: BookOpenText,
      showCondition: (currentUser) => !!currentUser.last_visited_study_option,
      colorScheme: {
        gradient: "from-slate-50 via-blue-50 to-slate-100",
        iconColor: "text-slate-600",
        textColor: "text-slate-800",
        hoverShadow: "hover:shadow-slate-500/25",
        glowColor: "from-slate-400 to-blue-500",
        darkGradient: "dark:from-slate-950/20 dark:via-blue-950/20 dark:to-slate-900/20",
        darkText: "dark:text-slate-200",
      },
    },
    {
      titleKey: "viewStatisticsTitle",
      descriptionKey: "viewStatisticsDescription",
      href: `${PATHS.STUDY.HOME}/statistics`,
      icon: BarChart3,
      colorScheme: {
        gradient: "from-indigo-50 via-blue-50 to-indigo-100",
        iconColor: "text-indigo-600",
        textColor: "text-indigo-800",
        hoverShadow: "hover:shadow-indigo-500/25",
        glowColor: "from-indigo-400 to-blue-500",
        darkGradient: "dark:from-indigo-950/20 dark:via-blue-950/20 dark:to-indigo-900/20",
        darkText: "dark:text-indigo-200",
      },
    },
    {
      titleKey: "checkRewardsTitle",
      descriptionKey: "checkRewardsDescription",
      href: `${PATHS.STUDY.HOME}/rewards-and-competitions`,
      icon: Gift,
      colorScheme: {
        gradient: "from-blue-50 via-slate-50 to-blue-100",
        iconColor: "text-blue-600",
        textColor: "text-blue-800",
        hoverShadow: "hover:shadow-blue-500/25",
        glowColor: "from-blue-400 to-slate-500",
        darkGradient: "dark:from-blue-950/20 dark:via-slate-950/20 dark:to-blue-900/20",
        darkText: "dark:text-blue-200",
      },
    },
  ];

  return (
    <div>
      <h2 className="mb-6 text-xl font-semibold bg-gradient-to-r from-[#074182] to-slate-600 bg-clip-text text-transparent dark:from-blue-200 dark:to-slate-400">
        {t("title")}
      </h2>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
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
              <Card className={`
                group relative h-full overflow-hidden border-0 transition-all duration-500 
                bg-gradient-to-br ${item.colorScheme.gradient} ${item.colorScheme.darkGradient}
                shadow-sm hover:shadow-2xl ${item.colorScheme.hoverShadow}
                hover:-translate-y-2 hover:scale-[1.03] hover:rotate-1
                cursor-pointer transform-gpu
              `}>
                {/* Background glow effects */}
                <div className={`
                  absolute -top-4 -right-4 h-20 w-20 rounded-full blur-2xl
                  bg-gradient-to-br ${item.colorScheme.glowColor}
                  opacity-0 transition-opacity duration-700 group-hover:opacity-15
                `} />
                <div className={`
                  absolute -bottom-4 -left-4 h-28 w-28 rounded-full blur-2xl
                  bg-gradient-to-br ${item.colorScheme.glowColor}
                  opacity-0 transition-opacity duration-700 group-hover:opacity-10
                `} />

                {/* Sparkle effects */}
                <div className="absolute top-3 right-3 opacity-0 transition-all duration-700 group-hover:opacity-60">
                  <Sparkles className="h-4 w-4 text-white/60 animate-pulse" />
                </div>

                <CardHeader className="relative pb-3">
                  <div className="flex items-center justify-between">
                    <div className="relative">
                      <item.icon className={`
                        mb-2 h-8 w-8 transition-all duration-500
                        ${item.colorScheme.iconColor}
                        group-hover:scale-125 group-hover:rotate-12 group-hover:drop-shadow-lg
                      `} />
                      {/* Icon glow */}
                      <div className={`
                        absolute inset-0 mb-2 h-8 w-8 rounded-full blur-md
                        ${item.colorScheme.iconColor.replace('text-', 'bg-')}
                        opacity-0 transition-opacity duration-500 group-hover:opacity-30
                      `} />
                    </div>
                    
                    <div className="relative">
                      <ArrowRight className={`
                        h-5 w-5 text-muted-foreground transition-all duration-500
                        group-hover:translate-x-2 group-hover:scale-110 
                        ${item.colorScheme.iconColor} group-hover:drop-shadow-md
                      `} />
                      {/* Arrow trail effect */}
                      <ArrowRight className={`
                        absolute inset-0 h-5 w-5 transition-all duration-700
                        ${item.colorScheme.iconColor} opacity-0 
                        group-hover:opacity-30 group-hover:translate-x-1 group-hover:scale-90
                      `} />
                    </div>
                  </div>
                  
                  <CardTitle className={`
                    text-lg font-semibold transition-all duration-300
                    ${item.colorScheme.textColor} ${item.colorScheme.darkText}
                    group-hover:scale-105 transform-gpu
                  `}>
                    {title}
                  </CardTitle>
                </CardHeader>
                
                <CardContent className="relative">
                  <p className={`
                    text-sm transition-all duration-300
                    ${item.colorScheme.textColor.replace('800', '600')} 
                    ${item.colorScheme.darkText.replace('200', '300')}
                    group-hover:scale-102 transform-gpu
                  `}>
                    {t(item.descriptionKey)}
                  </p>
                  
                  {/* Floating particles */}
                  <div className={`
                    absolute bottom-4 right-6 h-1 w-1 rounded-full
                    ${item.colorScheme.iconColor.replace('text-', 'bg-')}
                    opacity-0 transition-all duration-700 
                    group-hover:opacity-60 group-hover:translate-y-2
                  `} />
                  <div className={`
                    absolute bottom-6 right-4 h-1 w-1 rounded-full
                    ${item.colorScheme.iconColor.replace('text-', 'bg-').replace('500', '400')}
                    opacity-0 transition-all duration-900 
                    group-hover:opacity-40 group-hover:translate-y-3
                  `} />
                  <div className={`
                    absolute bottom-8 right-8 h-1 w-1 rounded-full
                    ${item.colorScheme.iconColor.replace('text-', 'bg-').replace('500', '300')}
                    opacity-0 transition-all duration-1100 
                    group-hover:opacity-20 group-hover:translate-y-4
                  `} />
                </CardContent>
                
                {/* Bottom gradient highlight */}
                <div className={`
                  absolute bottom-0 left-0 right-0 h-1 
                  bg-gradient-to-r ${item.colorScheme.glowColor}
                  opacity-0 transition-opacity duration-500 group-hover:opacity-60
                `} />
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
};
