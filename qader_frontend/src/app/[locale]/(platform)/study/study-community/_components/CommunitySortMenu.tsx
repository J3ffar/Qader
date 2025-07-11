"use client";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import {
  ListFilter,
  ArrowUpDown,
  Pin,
  ThumbsUp,
  Sparkles,
  XCircle,
} from "lucide-react";

type SortOption =
  | "-created_at"
  | "created_at"
  | "-like_count"
  | "-is_pinned"
  | "is_closed";

const SORT_OPTIONS: {
  value: SortOption;
  label: string;
  icon: React.ReactNode;
}[] = [
  {
    value: "-created_at",
    label: "الأحدث أولاً",
    icon: <Sparkles className="me-2 h-4 w-4" />,
  },
  {
    value: "-like_count",
    label: "الأكثر إعجابًا",
    icon: <ThumbsUp className="me-2 h-4 w-4" />,
  },
  {
    value: "-is_pinned",
    label: "المثبتة أولاً",
    icon: <Pin className="me-2 h-4 w-4" />,
  },
  {
    value: "created_at",
    label: "الأقدم أولاً",
    icon: <ArrowUpDown className="me-2 h-4 w-4" />,
  },
  {
    value: "is_closed",
    label: "المغلقة فقط",
    icon: <XCircle className="me-2 h-4 w-4" />,
  },
];

interface CommunitySortMenuProps {
  currentSort: SortOption;
  onSortChange: (sort: SortOption) => void;
}

export function CommunitySortMenu({
  currentSort,
  onSortChange,
}: CommunitySortMenuProps) {
  const currentOption =
    SORT_OPTIONS.find((opt) => opt.value === currentSort) || SORT_OPTIONS[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline">
          <ListFilter className="me-2 h-4 w-4" />
          {currentOption.label}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>ترتيب حسب</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {SORT_OPTIONS.map((option) => (
          <DropdownMenuItem
            key={option.value}
            onClick={() => onSortChange(option.value)}
            className="cursor-pointer"
          >
            {option.icon}
            {option.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
