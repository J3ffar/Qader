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
  1: "Very Easy",
  2: "Easy",
  3: "Medium",
  4: "Hard",
  5: "Very Hard",
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
      <ArrowUpDown className="ml-2 h-4 w-4" />
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
          <span className="sr-only">Open menu</span>
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleView(question.id)}>
          View Details
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleEdit(question.id)}>
          Edit
        </DropdownMenuItem>
        <DropdownMenuItem
          className="text-red-500"
          onClick={() => handleDelete(question.id)}
        >
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export const getColumns = (): ColumnDef<AdminQuestion>[] => [
  { accessorKey: "id", header: "ID" },
  {
    accessorKey: "image",
    header: "Image",
    cell: ({ row }) =>
      row.original.image ? (
        <img
          src={row.original.image}
          alt="Question"
          className="h-12 w-12 object-cover rounded-md"
        />
      ) : (
        <div className="h-12 w-12 flex items-center justify-center bg-muted rounded-md text-muted-foreground">
          <ImageIcon size={20} />
        </div>
      ),
    enableSorting: false, // Cannot sort by image as per backend docs
  },
  {
    accessorKey: "question_text",
    header: "Question",
    cell: ({ row }) => (
      <div className="max-w-lg truncate">{row.original.question_text}</div>
    ),
  },
  {
    accessorKey: "difficulty",
    header: ({ column }) => (
      <SortableHeader column={column}>Difficulty</SortableHeader>
    ),
    cell: ({ row }) => (
      <span>{difficultyMap[row.original.difficulty] || "N/A"}</span>
    ),
  },
  {
    accessorKey: "total_usage_count",
    header: ({ column }) => (
      <SortableHeader column={column}>Usage</SortableHeader>
    ),
  },
  {
    accessorKey: "is_active",
    header: ({ column }) => (
      <SortableHeader column={column}>Status</SortableHeader>
    ),
    cell: ({ row }) => (
      <Badge variant={row.original.is_active ? "default" : "outline"}>
        {row.original.is_active ? "Active" : "Inactive"}
      </Badge>
    ),
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => (
      <SortableHeader column={column}>Created</SortableHeader>
    ),
    cell: ({ row }) => new Date(row.original.created_at).toLocaleDateString(),
  },
  {
    id: "actions",
    cell: ActionsCell,
  },
];
