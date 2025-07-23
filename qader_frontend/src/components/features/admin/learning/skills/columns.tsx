"use client";

import { ColumnDef, Row, Table } from "@tanstack/react-table";
import { AdminSkill } from "@/types/api/admin/learning.types";
import { Button } from "@/components/ui/button";
import { MoreHorizontal } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const ActionsCell = ({
  row,
  table,
}: {
  row: Row<AdminSkill>;
  table: Table<AdminSkill>;
}) => {
  const { handleEdit, handleDelete } = table.options.meta as any;
  const skill = row.original;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-8 w-8 p-0">
          <span className="sr-only">Open menu</span>
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleEdit(skill.id)}>
          Edit
        </DropdownMenuItem>
        <DropdownMenuItem
          className="text-red-500"
          onClick={() => handleDelete(skill.id)}
        >
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export const getColumns = (): ColumnDef<AdminSkill>[] => [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "name", header: "Name" },
  {
    accessorKey: "subsection_name",
    header: "Parent Sub-Section",
  },
  {
    accessorKey: "description",
    header: "Description",
    cell: ({ row }) => (
      <div className="max-w-md truncate">
        {row.original.description || "N/A"}
      </div>
    ),
  },
  {
    accessorKey: "created_at",
    header: "Created",
    cell: ({ row }) => new Date(row.original.created_at).toLocaleDateString(),
  },
  { id: "actions", cell: ActionsCell },
];
