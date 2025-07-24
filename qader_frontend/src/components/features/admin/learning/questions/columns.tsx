"use client";

import { ColumnDef, Row, Table } from "@tanstack/react-table";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { AdminQuestion } from "@/types/api/admin/learning.types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowUpDown, MoreHorizontal, Image as ImageIcon } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const difficultyMap: { [key: number]: string } = {
  1: "سهل جداً",
  2: "سهل",
  3: "متوسط",
  4: "صعب",
  5: "صعب جداً",
};

// Reusable component for sortable headers
const SortableHeader = ({
  column,
  children,
}: {
  column: any;
  children: React.ReactNode;
}) => {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const handleSort = () => {
    const params = new URLSearchParams(searchParams.toString());
    const currentOrder = params.get("ordering");
    const columnId = column.id;

    let newOrder: string | null = columnId;
    if (currentOrder === columnId) newOrder = `-${columnId}`;
    else if (currentOrder === `-${columnId}`) newOrder = null;

    if (newOrder) params.set("ordering", newOrder);
    else params.delete("ordering");

    router.replace(`${pathname}?${params.toString()}`);
  };

  return (
    <Button variant="ghost" onClick={handleSort}>
      {children}
      <ArrowUpDown className="rtl:mr-2 ltr:ml-2 h-4 w-4" />
    </Button>
  );
};

// Actions Cell Component
const ActionsCell = ({
  row,
  table,
}: {
  row: Row<AdminQuestion>;
  table: Table<AdminQuestion>;
}) => {
  const { handleEdit, handleDelete, handleView } = table.options.meta as any;
  const question = row.original;

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-8 w-8 p-0">
          <span className="sr-only">فتح القائمة</span>
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuItem onClick={() => handleView(question.id)}>
          عرض التفاصيل
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleEdit(question.id)}>
          تعديل
        </DropdownMenuItem>
        <DropdownMenuItem
          className="text-red-500 focus:text-red-500 focus:bg-red-50 dark:focus:bg-red-900/40"
          onClick={() => handleDelete(question.id)}
        >
          حذف
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export const getColumns = (): ColumnDef<AdminQuestion>[] => [
  { accessorKey: "id", header: "المعرف" },
  {
    accessorKey: "image",
    header: "صورة",
    cell: ({ row }) =>
      row.original.image ? (
        <img
          src={row.original.image}
          alt="صورة السؤال"
          className="h-12 w-12 object-cover rounded-md"
        />
      ) : (
        <div className="h-12 w-12 flex items-center justify-center bg-muted rounded-md text-muted-foreground">
          <ImageIcon size={20} />
        </div>
      ),
    enableSorting: false,
  },
  {
    accessorKey: "question_text",
    header: "السؤال",
    cell: ({ row }) => (
      <div className="max-w-lg truncate">{row.original.question_text}</div>
    ),
  },
  {
    header: "القسم",
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
      <SortableHeader column={column}>مستوى الصعوبة</SortableHeader>
    ),
    cell: ({ row }) => (
      <span>{difficultyMap[row.original.difficulty] || "N/A"}</span>
    ),
  },
  {
    accessorKey: "total_usage_count",
    header: ({ column }) => (
      <SortableHeader column={column}>الاستخدام</SortableHeader>
    ),
  },
  {
    accessorKey: "is_active",
    header: ({ column }) => (
      <SortableHeader column={column}>الحالة</SortableHeader>
    ),
    cell: ({ row }) => (
      <Badge variant={row.original.is_active ? "default" : "outline"}>
        {row.original.is_active ? "نشط" : "غير نشط"}
      </Badge>
    ),
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => (
      <SortableHeader column={column}>تاريخ الإنشاء</SortableHeader>
    ),
    cell: ({ row }) =>
      new Date(row.original.created_at).toLocaleDateString("ar-EG"), // Use locale for date
  },
  {
    id: "actions",
    cell: ActionsCell,
  },
];
