"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useDebounce } from "@/hooks/use-debounce";
import { X } from "lucide-react";
import { queryKeys } from "@/constants/queryKeys";
import {
  getAdminAllSections,
  getAdminAllSubSections,
  getAdminAllSkills,
} from "@/services/api/admin/learning.service";

interface QuestionsTableToolbarProps {
  onFilterChange: (params: Record<string, string | null>) => void;
  currentFilters: Record<string, any>;
}

export function QuestionsTableToolbar({
  onFilterChange,
  currentFilters,
}: QuestionsTableToolbarProps) {
  const [search, setSearch] = useState(currentFilters.search ?? "");
  const [selectedSection, setSelectedSection] = useState<string>(
    currentFilters.subsection__section__id ?? ""
  );
  const [selectedSubsection, setSelectedSubsection] = useState<string>(
    currentFilters.subsection__id ?? ""
  );
  const [selectedSkill, setSelectedSkill] = useState<string>(
    currentFilters.skill__id ?? ""
  );

  const debouncedSearch = useDebounce(search, 500);

  useEffect(() => {
    if (debouncedSearch !== (currentFilters.search ?? "")) {
      onFilterChange({ search: debouncedSearch || null });
    }
  }, [debouncedSearch]);

  const { data: sections } = useQuery({
    queryKey: queryKeys.admin.learning.sections.list({ all: true }),
    queryFn: getAdminAllSections,
  });

  const { data: subsections } = useQuery({
    queryKey: queryKeys.admin.learning.subsections.list({
      sectionId: selectedSection,
    }),
    queryFn: () => getAdminAllSubSections(Number(selectedSection)),
    enabled: !!selectedSection,
  });

  const { data: skills } = useQuery({
    queryKey: queryKeys.admin.learning.skills.list({
      subsectionId: selectedSubsection,
    }),
    queryFn: () => getAdminAllSkills(Number(selectedSubsection)),
    enabled: !!selectedSubsection,
  });

  const handleSectionChange = (value: string) => {
    const newSection = value === "all" ? "" : value;
    setSelectedSection(newSection);
    setSelectedSubsection("");
    setSelectedSkill("");
    onFilterChange({
      subsection__section__id: newSection || null,
      subsection__id: null,
      skill__id: null,
    });
  };

  const handleSubsectionChange = (value: string) => {
    const newSubsection = value === "all" ? "" : value;
    setSelectedSubsection(newSubsection);
    setSelectedSkill("");
    onFilterChange({ 
      subsection__id: newSubsection || null, 
      skill__id: null 
    });
  };

  const handleSkillChange = (value: string) => {
    const newSkill = value === "all" ? "" : value;
    setSelectedSkill(newSkill);
    onFilterChange({ skill__id: newSkill || null });
  };

  const handleClearFilters = () => {
    setSearch("");
    setSelectedSection("");
    setSelectedSubsection("");
    setSelectedSkill("");
    onFilterChange({
      search: null,
      subsection__section__id: null,
      subsection__id: null,
      skill__id: null,
    });
  };

  const hasActiveFilters = 
    search || 
    selectedSection || 
    selectedSubsection || 
    selectedSkill;

  return (
    <div className="flex items-center gap-2 p-4 border-b flex-wrap">
      <Input
        placeholder="ابحث في الأسئلة..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-xs"
      />

      <Select
        value={selectedSection || "all"}
        onValueChange={handleSectionChange}
        dir="rtl"
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="اختر القسم الرئيسي" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all" className="font-medium">
            كل الأقسام الرئيسية
          </SelectItem>
          {sections?.results.map((s) => (
            <SelectItem key={s.id} value={s.id.toString()}>
              {s.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={selectedSubsection || "all"}
        onValueChange={handleSubsectionChange}
        disabled={!selectedSection}
        dir="rtl"
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="اختر القسم الفرعي" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all" className="font-medium">
            كل الأقسام الفرعية
          </SelectItem>
          {subsections?.results.map((s) => (
            <SelectItem key={s.id} value={s.id.toString()}>
              {s.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={selectedSkill || "all"}
        onValueChange={handleSkillChange}
        disabled={!selectedSubsection}
        dir="rtl"
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="اختر المهارة" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all" className="font-medium">
            كل المهارات
          </SelectItem>
          {skills?.results.map((s) => (
            <SelectItem key={s.id} value={s.id.toString()}>
              {s.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {hasActiveFilters && (
        <Button
          variant="ghost"
          onClick={handleClearFilters}
          className="h-8 px-2 lg:px-3"
        >
          <X className="rtl:ml-2 ltr:mr-2 h-4 w-4" />
          مسح الفلترة
        </Button>
      )}
    </div>
  );
}
