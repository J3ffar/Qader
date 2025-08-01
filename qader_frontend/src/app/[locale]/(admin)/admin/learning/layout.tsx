// qader_frontend/src/app/[locale]/(admin)/admin/learning/layout.tsx
"use client";

import { ReactNode, useMemo } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PATHS } from "@/constants/paths";
import { queryKeys } from "@/constants/queryKeys";
import {
  getAdminQuestions,
  getAdminSkills,
  getAdminSubSections,
  getAdminSections,
} from "@/services/api/admin/learning.service";

// Base config without counts
const BASE_TABS = [
  {
    value: "questions",
    label: "بنك الأسئلة",
    path: PATHS.ADMIN.LEARNING.QUESTIONS,
  },
  {
    value: "subsections",
    label: "الأقسام الفرعية",
    path: PATHS.ADMIN.LEARNING.SUBSECTIONS,
  },
  { value: "skills", label: "المهارات", path: PATHS.ADMIN.LEARNING.SKILLS },
  {
    value: "sections",
    label: "الأقسام الرئيسية",
    path: PATHS.ADMIN.LEARNING.SECTIONS,
  },
];

export default function LearningManagementLayout({
  children,
}: {
  children: ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

  // --- Efficiently fetch counts for each entity ---
  // We only request 1 item per page because we only need the 'count' from the paginated response.
  const { data: questionsCount } = useQuery({
    queryKey: queryKeys.admin.learning.questions.list({ countOnly: true }),
    queryFn: () => getAdminQuestions({ page_size: 1 }),
    select: (data) => data.count,
  });

  const { data: skillsCount } = useQuery({
    queryKey: queryKeys.admin.learning.skills.list({ countOnly: true }),
    queryFn: () => getAdminSkills({ page_size: 1 }),
    select: (data) => data.count,
  });

  const { data: subsectionsCount } = useQuery({
    queryKey: queryKeys.admin.learning.subsections.list({ countOnly: true }),
    queryFn: () => getAdminSubSections({ page_size: 1 }),
    select: (data) => data.count,
  });

  const { data: sectionsCount } = useQuery({
    queryKey: queryKeys.admin.learning.sections.list({ countOnly: true }),
    queryFn: () => getAdminSections({ page_size: 1 }),
    select: (data) => data.count,
  });

  // --- Dynamically generate tabs with counts ---
  const TABS_CONFIG = useMemo(() => {
    const counts: Record<string, number | undefined> = {
      questions: questionsCount,
      skills: skillsCount,
      subsections: subsectionsCount,
      sections: sectionsCount,
    };
    return BASE_TABS.map((tab) => {
      const count = counts[tab.value];
      return {
        ...tab,
        // Show count if available, otherwise show a loading indicator '...'
        label: `${tab.label} (${typeof count === "number" ? count : "..."})`,
      };
    });
  }, [questionsCount, skillsCount, subsectionsCount, sectionsCount]);

  const currentTab =
    TABS_CONFIG.find((tab) => pathname.includes(tab.path))?.value ||
    "questions";

  const handleTabChange = (value: string) => {
    const tab = TABS_CONFIG.find((t) => t.value === value);
    if (tab) {
      router.push(tab.path);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          إدارة المحتوى التعليمي
        </h1>
        <p className="text-muted-foreground">
          إدارة الأسئلة، المهارات، الأقسام الفرعية، والأقسام الرئيسية للمنصة
          التعليمية.
        </p>
      </div>
      <Tabs
        value={currentTab}
        onValueChange={handleTabChange}
        dir="rtl"
        className="w-full"
      >
        <TabsList className="w-full">
          {TABS_CONFIG.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
      <div className="pt-4">{children}</div>
    </div>
  );
}
