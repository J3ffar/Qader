"use client";

import { ColumnDef, Row, Table } from "@tanstack/react-table";
import { AdminSection } from "@/types/api/admin/learning.types";
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
  row: Row<AdminSection>;
  table: Table<AdminSection>;
}) => {
  const { handleEdit, handleDelete } = table.options.meta as any;
  const section = row.original;

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-8 w-8 p-0">
          <span className="sr-only">فتح القائمة</span>
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleEdit(section.id)}>
          تعديل
        </DropdownMenuItem>
        <DropdownMenuItem
          className="text-red-500 focus:text-red-500 focus:bg-red-50 dark:focus:bg-red-900/40"
          onClick={() => handleDelete(section.id)}
        >
          حذف
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export const getColumns = (): ColumnDef<AdminSection>[] => [
  { accessorKey: "id", header: "المعرف" },
  { accessorKey: "name", header: "الاسم" },
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
      new Date(row.original.created_at).toLocaleDateString("ar"),
  },
  { id: "actions", cell: ActionsCell },
];
