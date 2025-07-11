"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PostType } from "@/types/api/community.types";

interface CommunityFiltersProps {
  activeFilter: PostType;
  onFilterChange: (filter: PostType) => void;
}

const postTypeFilters: { label: string; value: PostType }[] = [
  { label: "النقاشات الدراسية", value: "discussion" },
  { label: "الإنجازات", value: "achievement" },
  { label: "طلب زميل", value: "partner_search" },
  { label: "النصائح والتجارب", value: "tip" },
  { label: "مسابقات شهرية", value: "competition" },
];

export function CommunityFilters({
  activeFilter,
  onFilterChange,
}: CommunityFiltersProps) {
  return (
    <div className="mb-6 flex justify-center">
      <Tabs
        defaultValue={activeFilter}
        onValueChange={(value) => onFilterChange(value as PostType)}
        dir="rtl"
      >
        <TabsList className="grid w-full grid-cols-2 sm:grid-cols-3 md:grid-cols-5">
          {postTypeFilters.map((filter) => (
            <TabsTrigger key={filter.value} value={filter.value}>
              {filter.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
    </div>
  );
}
