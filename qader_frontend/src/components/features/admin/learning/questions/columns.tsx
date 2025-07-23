"use client";

import { ColumnDef } from "@tanstack/react-table";
import { AdminQuestion } from "@/types/api/admin/learning.types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowUpDown, MoreHorizontal } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const difficultyMap: { [key: number]: string } = {
  1: "Very Easy",
  2: "Easy",
  3: "Medium",
  4: "Hard",
  5: "Very Hard",
};

export const getColumns = (
  onEdit: (id: number) => void,
  onDelete: (id: number) => void,
  onView: (id: number) => void
): ColumnDef<AdminQuestion>[] => [
  {
    accessorKey: "id",
    header: "ID",
  },
  {
    accessorKey: "question_text",
    header: "Question",
    cell: ({ row }) => (
      <div className="max-w-md truncate">{row.original.question_text}</div>
    ),
  },
  {
    header: "Hierarchy",
    cell: ({ row }) => {
      const { section, subsection, skill } = row.original;
      return (
        <div className="flex flex-col text-xs">
          <span>{section.name}</span>
          <span className="text-muted-foreground">
            {">"} {subsection.name}
          </span>
          {skill && (
            <span className="text-muted-foreground">
              {">>"} {skill.name}
            </span>
          )}
        </div>
      );
    },
  },
  {
    accessorKey: "difficulty",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Difficulty <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ row }) => (
      <span>{difficultyMap[row.original.difficulty] || "N/A"}</span>
    ),
  },
  {
    accessorKey: "total_usage_count",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Usage <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
  },
  {
    accessorKey: "is_active",
    header: "Status",
    cell: ({ row }) => (
      <Badge variant={row.original.is_active ? "default" : "outline"}>
        {row.original.is_active ? "Active" : "Inactive"}
      </Badge>
    ),
  },
  {
    id: "actions",
    cell: ({ row }) => (
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-8 w-8 p-0">
            <span className="sr-only">Open menu</span>
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => onView(row.original.id)}>
            View Details
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onEdit(row.original.id)}>
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem
            className="text-red-500"
            onClick={() => onDelete(row.original.id)}
          >
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];
