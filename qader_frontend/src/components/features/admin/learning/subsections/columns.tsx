"use client";

import { ColumnDef, Row, Table } from "@tanstack/react-table";
import { AdminSubSection } from "@/types/api/admin/learning.types";
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
  row: Row<AdminSubSection>;
  table: Table<AdminSubSection>;
}) => {
  const { handleEdit, handleDelete } = table.options.meta as any;
  const subsection = row.original;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-8 w-8 p-0">
          <span className="sr-only">Open menu</span>
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleEdit(subsection.id)}>
          Edit
        </DropdownMenuItem>
        <DropdownMenuItem
          className="text-red-500"
          onClick={() => handleDelete(subsection.id)}
        >
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export const getColumns = (): ColumnDef<AdminSubSection>[] => [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "name", header: "Name" },
  {
    accessorKey: "section_name",
    header: "Parent Section",
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
  { accessorKey: "order", header: "Order" },
  {
    accessorKey: "created_at",
    header: "Created",
    cell: ({ row }) => new Date(row.original.created_at).toLocaleDateString(),
  },
  { id: "actions", cell: ActionsCell },
];
