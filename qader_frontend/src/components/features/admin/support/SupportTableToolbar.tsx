"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button"; // Import Button
import { useTranslations } from "next-intl";
import { X } from "lucide-react"; // Import X icon

interface SupportTableToolbarProps {
  filters: Record<string, string>;
  onFilterChange: (key: string, value: string | null) => void;
}

export function SupportTableToolbar({
  filters,
  onFilterChange,
}: SupportTableToolbarProps) {
  const t = useTranslations("Admin.support");

  // A helper to determine if any filters are active
  const isFiltered = filters.search || filters.status || filters.priority;

  const handleClearFilters = () => {
    onFilterChange("search", null);
    onFilterChange("status", null);
    onFilterChange("priority", null);
  };

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
      <Input
        placeholder={t("filters.searchPlaceholder")}
        value={filters.search}
        onChange={(e) => onFilterChange("search", e.target.value)}
        className="h-10 max-w-sm"
      />
      <div className="flex items-center gap-2">
        <Select
          value={filters.status || "all"} // Use 'all' if filter is not set
          onValueChange={(v) =>
            onFilterChange("status", v === "all" ? null : v)
          }
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder={t("filters.status")} />
          </SelectTrigger>
          <SelectContent>
            {/* CORRECTED: Using "all" instead of "" */}
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="open">{t("statusLabels.open")}</SelectItem>
            <SelectItem value="pending_admin">
              {t("statusLabels.pending_admin")}
            </SelectItem>
            <SelectItem value="pending_user">
              {t("statusLabels.pending_user")}
            </SelectItem>
            <SelectItem value="closed">{t("statusLabels.closed")}</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={filters.priority || "all"} // Use 'all' if filter is not set
          onValueChange={(v) =>
            onFilterChange("priority", v === "all" ? null : v)
          }
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder={t("filters.priority")} />
          </SelectTrigger>
          <SelectContent>
            {/* CORRECTED: Using "all" instead of "" */}
            <SelectItem value="all">All Priorities</SelectItem>
            <SelectItem value="1">{t("priorityLabels.1")}</SelectItem>
            <SelectItem value="2">{t("priorityLabels.2")}</SelectItem>
            <SelectItem value="3">{t("priorityLabels.3")}</SelectItem>
          </SelectContent>
        </Select>

        {isFiltered && (
          <Button
            variant="ghost"
            onClick={handleClearFilters}
            className="h-10 px-2 lg:px-3"
          >
            {t("filters.clear")}
            <X className="ltr:ml-2 rtl:mr-2 h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
