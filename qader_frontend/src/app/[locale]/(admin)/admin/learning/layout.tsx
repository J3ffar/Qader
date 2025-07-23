"use client";

import { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PATHS } from "@/constants/paths";

const TABS_CONFIG = [
  {
    value: "questions",
    label: "Questions",
    path: PATHS.ADMIN.LEARNING.QUESTIONS,
  },
  { value: "skills", label: "Skills", path: PATHS.ADMIN.LEARNING.SKILLS },
  {
    value: "subsections",
    label: "Sub-Sections",
    path: PATHS.ADMIN.LEARNING.SUBSECTIONS,
  },
  { value: "sections", label: "Sections", path: PATHS.ADMIN.LEARNING.SECTIONS },
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
          Learning Management
        </h1>
        <p className="text-muted-foreground">
          Manage questions, skills, subsections, and sections for the learning
          platform.
        </p>
      </div>
      <Tabs
        value={currentTab}
        onValueChange={handleTabChange}
        className="w-full"
      >
        <TabsList>
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
