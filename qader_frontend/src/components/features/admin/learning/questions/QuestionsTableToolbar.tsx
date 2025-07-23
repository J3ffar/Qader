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
  // Initialize local state from the friendly URL filter props
  const [search, setSearch] = useState(currentFilters.search ?? "");
  const [selectedSection, setSelectedSection] = useState<string>(
    currentFilters.section ?? ""
  );
  const [selectedSubsection, setSelectedSubsection] = useState<string>(
    currentFilters.subsection ?? ""
  );
  const [selectedSkill, setSelectedSkill] = useState<string>(
    currentFilters.skill ?? ""
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

  // This query now correctly depends on the selectedSection state
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

  const handleClearFilters = () => {
    setSearch("");
    setSelectedSection("");
    setSelectedSubsection("");
    setSelectedSkill("");
    onFilterChange({
      search: null,
      section: null,
      subsection: null,
      skill: null,
    });
  };

  const isFiltered =
    !!currentFilters.search ||
    !!currentFilters.section ||
    !!currentFilters.subsection ||
    !!currentFilters.skill;

  return (
    <div className="flex items-center gap-2 p-4 border-b">
      <Input
        placeholder="Search questions..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-xs"
      />

      {/* --- REVISED SECTION SELECT --- */}
      <Select
        value={selectedSection}
        onValueChange={(value) => {
          const newSection = value || "";
          setSelectedSection(newSection);

          // When section changes, clear downstream filters and update URL
          setSelectedSubsection("");
          setSelectedSkill("");
          onFilterChange({
            section: newSection || null,
            subsection: null,
            skill: null,
          });
        }}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="All Sections" />
        </SelectTrigger>
        <SelectContent>
          {sections?.results.map((s) => (
            <SelectItem key={s.id} value={s.id.toString()}>
              {s.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Subsection and Skill Selects remain the same as the last version */}
      <Select
        value={selectedSubsection}
        onValueChange={(value) => {
          const newSubsection = value || "";
          setSelectedSubsection(newSubsection);
          setSelectedSkill("");
          onFilterChange({ subsection: newSubsection || null, skill: null });
        }}
        disabled={!selectedSection} // Disabling logic is now correct
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="All Subsections" />
        </SelectTrigger>
        <SelectContent>
          {subsections?.results.map((s) => (
            <SelectItem key={s.id} value={s.id.toString()}>
              {s.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={selectedSkill}
        onValueChange={(value) => {
          const newSkill = value || "";
          setSelectedSkill(newSkill);
          onFilterChange({ skill: newSkill || null });
        }}
        disabled={!selectedSubsection}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="All Skills" />
        </SelectTrigger>
        <SelectContent>
          {skills?.results.map((s) => (
            <SelectItem key={s.id} value={s.id.toString()}>
              {s.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {isFiltered && (
        <Button
          variant="ghost"
          onClick={handleClearFilters}
          className="h-8 px-2 lg:px-3"
        >
          <X className="mr-2 h-4 w-4" />
          Clear
        </Button>
      )}
    </div>
  );
}
