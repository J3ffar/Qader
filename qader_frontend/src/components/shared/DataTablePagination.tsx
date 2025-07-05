import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DataTablePaginationProps {
  page: number;
  pageCount: number;
  setPage: (page: number) => void;
  canPreviousPage: boolean;
  canNextPage: boolean;
  isFetching?: boolean; // To disable controls during refetch
  className?: string;
  itemsPerPage?: number; // Optional, if we want to show a page size selector in the future
}

export function DataTablePagination({
  page,
  pageCount,
  setPage,
  canPreviousPage,
  canNextPage,
  isFetching = false,
  className,
}: DataTablePaginationProps) {
  const t = useTranslations("Common.DataTablePagination");

  if (pageCount <= 1) {
    return null; // Don't render pagination if there's only one page
  }

  return (
    <div
      className={cn("flex items-center justify-between px-2 pt-4", className)}
      dir="ltr"
    >
      <div className="flex-1 text-sm text-muted-foreground">
        {/* We can add total item count here in the future if needed */}
      </div>
      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          className="hidden h-8 w-8 p-0 lg:flex"
          onClick={() => setPage(1)}
          disabled={!canPreviousPage || isFetching}
          aria-label={t("firstPage")}
        >
          <ChevronsLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          className="h-8 w-8 p-0"
          onClick={() => setPage(page - 1)}
          disabled={!canPreviousPage || isFetching}
          aria-label={t("previousPage")}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <div className="flex w-[100px] items-center justify-center text-sm font-medium">
          {t("pageInfo", { currentPage: page, totalPages: pageCount })}
        </div>
        <Button
          variant="outline"
          className="h-8 w-8 p-0"
          onClick={() => setPage(page + 1)}
          disabled={!canNextPage || isFetching}
          aria-label={t("nextPage")}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          className="hidden h-8 w-8 p-0 lg:flex"
          onClick={() => setPage(pageCount)}
          disabled={!canNextPage || isFetching}
          aria-label={t("lastPage")}
        >
          <ChevronsRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
