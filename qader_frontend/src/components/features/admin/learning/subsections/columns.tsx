// qader_frontend/src/components/features/admin/learning/subsections/columns.tsx
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
          <span className="sr-only">فتح القائمة</span>
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleEdit(subsection.id)}>
          تعديل
        </DropdownMenuItem>
        <DropdownMenuItem
          className="text-red-500 focus:text-red-500 focus:bg-red-50 dark:focus:bg-red-900/40"
          onClick={() => handleDelete(subsection.id)}
        >
          حذف
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export const getColumns = (): ColumnDef<AdminSubSection>[] => [
  { accessorKey: "id", header: "المعرف" },
  { accessorKey: "name", header: "الاسم" },
  {
    accessorKey: "section_name",
    header: "القسم الرئيسي",
  },
  {
    accessorKey: "description",
    header: "الوصف",
    cell: ({ row }) => (
      <div className="max-w-md truncate">
        {row.original.description || "لا يوجد"}
      </div>
    ),
  },
  { accessorKey: "order", header: "الترتيب" },
  {
    accessorKey: "created_at",
    header: "تاريخ الإنشاء",
    cell: ({ row }) =>
      new Date(row.original.created_at).toLocaleDateString("ar-EG"),
  },
  { id: "actions", cell: ActionsCell },
];