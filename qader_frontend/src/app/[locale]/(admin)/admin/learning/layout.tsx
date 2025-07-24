"use client";

import { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PATHS } from "@/constants/paths";

const TABS_CONFIG = [
  {
    value: "questions",
    label: "بنك الأسئلة",
    path: PATHS.ADMIN.LEARNING.QUESTIONS,
  },
  {
    value: "sections",
    label: "الأقسام الرئيسية",
    path: PATHS.ADMIN.LEARNING.SECTIONS,
  },
  {
    value: "subsections",
    label: "الأقسام الفرعية",
    path: PATHS.ADMIN.LEARNING.SUBSECTIONS,
  },
  { value: "skills", label: "المهارات", path: PATHS.ADMIN.LEARNING.SKILLS },
];

export default function LearningManagementLayout({
  children,
}: {
  children: ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

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
      <div>{children}</div>
    </div>
  );
}
