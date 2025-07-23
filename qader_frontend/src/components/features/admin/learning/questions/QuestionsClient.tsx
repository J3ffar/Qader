"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/shared/DataTable";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { queryKeys } from "@/constants/queryKeys";
import { getAdminQuestions } from "@/services/api/admin/learning.service";
import { getColumns } from "./columns"; // We will update this file next
import { QuestionFormDialog } from "./QuestionFormDialog";
import { DeleteQuestionDialog } from "./DeleteQuestionDialog";
import { ViewQuestionDialog } from "./ViewQuestionDialog";
import { QuestionsTableToolbar } from "./QuestionsTableToolbar"; // New component for filters

const ITEMS_PER_PAGE = 20;

export function QuestionsClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Dialog states
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [selectedQuestionId, setSelectedQuestionId] = useState<number | null>(
    null
  );

  // Read all filter/sort/pagination state from the URL
  const filters = useMemo(() => {
    const params: Record<string, any> = {
      page: searchParams.get("page") ?? "1",
      search: searchParams.get("search") ?? "",
      ordering: searchParams.get("ordering") ?? "",
      subsection__section__id: searchParams.get("section") ?? "",
      subsection__id: searchParams.get("subsection") ?? "",
      skill__id: searchParams.get("skill") ?? "",
    };
    // Remove empty keys
    Object.keys(params).forEach((key) => {
      if (!params[key]) delete params[key];
    });
    return params;
  }, [searchParams]);

  const { data, isLoading, isFetching, isError, error } = useQuery({
    queryKey: queryKeys.admin.learning.questions.list(filters),
    queryFn: () => getAdminQuestions(filters),
    placeholderData: (prev) => prev,
  });

  const handleEdit = (id: number) => {
    setSelectedQuestionId(id);
    setIsFormOpen(true);
  };
  const handleDelete = (id: number) => {
    setSelectedQuestionId(id);
    setIsDeleteOpen(true);
  };
  const handleView = (id: number) => {
    setSelectedQuestionId(id);
    setIsViewOpen(true);
  };

  const handleCloseDialogs = () => {
    setIsFormOpen(false);
    setIsDeleteOpen(false);
    setIsViewOpen(false);
    setSelectedQuestionId(null);
  };

  const columns = useMemo(() => getColumns(), []); // We'll remove handlers from here and place them in the row menu
  const pageCount = data?.count ? Math.ceil(data.count / ITEMS_PER_PAGE) : 0;
  const currentPage = parseInt(filters.page?.toString() ?? "1", 10);

  if (isError) return <div>Error: {error.message}</div>;

  const handleSetUrlParams = (newParams: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(newParams).forEach(([key, value]) => {
      if (value) params.set(key, value);
      else params.delete(key);
    });
    // Always reset to page 1 when filters (not page itself) change
    if (!("page" in newParams)) {
      params.set("page", "1");
    }
    router.replace(`${pathname}?${params.toString()}`);
  };

  return (
    <div className="space-y-4">
      <QuestionFormDialog
        isOpen={isFormOpen}
        onClose={handleCloseDialogs}
        questionId={selectedQuestionId}
      />
      <DeleteQuestionDialog
        isOpen={isDeleteOpen}
        onClose={handleCloseDialogs}
        questionId={selectedQuestionId}
      />
      <ViewQuestionDialog
        isOpen={isViewOpen}
        onClose={handleCloseDialogs}
        questionId={selectedQuestionId}
      />

      <div className="flex items-center justify-between gap-2">
        <h2 className="text-2xl font-bold tracking-tight">Questions</h2>
        <Button
          onClick={() => {
            setSelectedQuestionId(null);
            setIsFormOpen(true);
          }}
        >
          Add Question
        </Button>
      </div>

      <div className="rounded-md border">
        <QuestionsTableToolbar
          onFilterChange={handleSetUrlParams}
          currentFilters={filters}
        />
        <DataTable
          columns={columns}
          data={data?.results ?? []}
          isLoading={isLoading}
          context={{ handleEdit, handleDelete, handleView }} // Pass actions via context
        />
      </div>

      <DataTablePagination
        page={currentPage}
        pageCount={pageCount}
        setPage={(newPage) => handleSetUrlParams({ page: newPage.toString() })}
        canPreviousPage={currentPage > 1}
        canNextPage={currentPage < pageCount}
        isFetching={isFetching}
      />
    </div>
  );
}
