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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useEffect, useMemo, useRef } from "react";
import katex from "katex";
import fromString, { htmlToText } from "html-to-text";

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

const RichContentViewer = ({ htmlContent }: { htmlContent: string | null }) => {
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contentRef.current && htmlContent) {
      const tempDiv = document.createElement("div");
      tempDiv.innerHTML = htmlContent;

      const katexNodes = tempDiv.querySelectorAll<HTMLElement>(
        "span[data-katex-node]"
      );

      katexNodes.forEach((node) => {
        const latex = node.dataset.latex || "";
        if (latex) {
          try {
            // Render KaTeX to a new element and replace the placeholder
            const katexElement = document.createElement("span");
            katex.render(latex, katexElement, {
              throwOnError: false,
              displayMode: false,
            });
            node.replaceWith(katexElement);
          } catch (e) {
            console.error("KaTeX rendering error:", e);
            node.textContent = `[Error: ${latex}]`;
          }
        }
      });
      // Clear the ref and append the processed content
      contentRef.current.innerHTML = "";
      contentRef.current.appendChild(tempDiv);
    }
  }, [htmlContent]);

  if (!htmlContent) return null;

  return (
    <div
      ref={contentRef}
      className="prose prose-sm dark:prose-invert max-w-none [&_p]:my-2"
    />
  );
};

const QuestionTextCell = ({ row }: { row: Row<AdminQuestion> }) => {
  const fullHtml = row.original.question_text;
  const maxLength = 75;

  const plainText = useMemo(() => {
    if (!fullHtml) return "";

    const katexRegex =
      /(<span data-katex-node.*?<\/span>|<span data-latex.*?<\/span>|<span class="katex".*?<\/span>)/g;
    const textWithPlaceholders = fullHtml.replace(katexRegex, " [معادلة] ");

    return htmlToText(textWithPlaceholders, {
      wordwrap: false,
      selectors: [{ selector: "a", options: { ignoreHref: true } }],
    });
  }, [fullHtml]);

  const isLong = plainText.length > maxLength;
  const truncatedText = isLong
    ? `${plainText.slice(0, maxLength)}...`
    : plainText;

  if (!isLong) {
    return (
      <div className="min-w-[250px] whitespace-normal break-words font-medium">
        {/* We display the clean text directly when it's short */}
        {plainText}
      </div>
    );
  }

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="min-w-[250px] whitespace-normal break-words font-medium cursor-default">
            {truncatedText}
          </div>
        </TooltipTrigger>
        <TooltipContent className="max-w-lg border p-2 rounded-md shadow-lg">
          {/* The tooltip still correctly renders the full rich content */}
          <RichContentViewer htmlContent={fullHtml} />
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
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
  {
    accessorKey: "id",
    header: "المعرف",
    // HIDDEN: Hide on mobile, show on medium screens and up.
    cell: ({ row }) => <span className="font-mono">{row.original.id}</span>,
    meta: {
      className: "hidden md:table-cell",
    },
  },
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
    cell: QuestionTextCell,
  },
  {
    header: "القسم",
    // HIDDEN: This detailed hierarchy is hidden on mobile to save space.
    cell: ({ row }) => {
      const { section, subsection, skill } = row.original;
      return (
        <div className="flex flex-col text-xs min-w-[150px]">
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
    meta: {
      className: "hidden lg:table-cell",
    },
  },
  {
    accessorKey: "difficulty",
    header: ({ column }) => (
      <SortableHeader column={column}>الصعوبة</SortableHeader>
    ),
    // HIDDEN: Difficulty is less critical on the mobile list view.
    cell: ({ row }) => (
      <span>{difficultyMap[row.original.difficulty] || "N/A"}</span>
    ),
    meta: {
      className: "hidden lg:table-cell",
    },
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
    meta: {
      className: "hidden md:table-cell",
    },
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => (
      <SortableHeader column={column}>تاريخ الإنشاء</SortableHeader>
    ),
    cell: ({ row }) =>
      new Date(row.original.created_at).toLocaleDateString("ar"),
    meta: {
      className: "hidden xl:table-cell",
    },
  },
  {
    id: "actions",
    cell: ActionsCell,
  },
];
