"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PATHS } from "@/constants/paths";
import { PostType } from "@/types/api/community.types";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navTabs: { label: string; value: PostType; path: string }[] = [
  {
    label: "النقاشات الدراسية",
    value: "discussion",
    path: PATHS.STUDY.COMMUNITY_DISCUSSION,
  },
  {
    label: "الإنجازات",
    value: "achievement",
    path: PATHS.STUDY.COMMUNITY_ACHIEVEMENT,
  },
  {
    label: "طلب زميل",
    value: "partner_search",
    path: PATHS.STUDY.COMMUNITY_PARTNER_SEARCH,
  },
  { label: "النصائح والتجارب", value: "tip", path: PATHS.STUDY.COMMUNITY_TIPS },
  {
    label: "مسابقات شهرية",
    value: "competition",
    path: PATHS.STUDY.COMMUNITY_COMPETITIONS,
  },
];

export function CommunityNavTabs() {
  const pathname = usePathname();
  const activeTabValue =
    navTabs.find((tab) => pathname.includes(tab.path))?.value || "discussion";

  return (
    <Tabs value={activeTabValue} dir="rtl">
      <TabsList className="grid w-full grid-cols-2 sm:grid-cols-3 md:grid-cols-5">
        {navTabs.map((tab) => (
          <TabsTrigger key={tab.value} value={tab.value} asChild>
            <Link href={tab.path}>{tab.label}</Link>
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
