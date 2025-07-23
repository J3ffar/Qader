"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/shared/DataTable";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { useDebounce } from "@/hooks/use-debounce";
import { queryKeys } from "@/constants/queryKeys";
import { getAdminQuestions } from "@/services/api/admin/learning.service";
import { getColumns } from "./columns";
import { QuestionFormDialog } from "./QuestionFormDialog";
import { DeleteQuestionDialog } from "./DeleteQuestionDialog";
import { ViewQuestionDialog } from "./ViewQuestionDialog";

const ITEMS_PER_PAGE = 20;

export function QuestionsClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false); // Add state for view dialog
  const [selectedQuestionId, setSelectedQuestionId] = useState<number | null>(
    null
  );

  const page = parseInt(searchParams.get("page") ?? "1", 10);
  const search = searchParams.get("search") ?? "";
  const debouncedSearch = useDebounce(search, 500);

  const handleSetUrlParam = (key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    if (key === "search") params.set("page", "1");
    router.replace(`${pathname}?${params.toString()}`);
  };

  const filters = useMemo(
    () => ({ page, search: debouncedSearch }),
    [page, debouncedSearch]
  );

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

  const columns = useMemo(
    () => getColumns(handleEdit, handleDelete, handleView),
    []
  );
  const pageCount = data?.count ? Math.ceil(data.count / ITEMS_PER_PAGE) : 0;

  if (isError) return <div>Error: {error.message}</div>;

  return (
    <div className="space-y-4">
      {/* All dialogs are now present and correctly wired */}
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
        <Input
          placeholder="Search questions..."
          value={search}
          onChange={(e) => handleSetUrlParam("search", e.target.value)}
          className="max-w-sm"
        />
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
        <DataTable
          columns={columns}
          data={data?.results ?? []}
          isLoading={isLoading}
        />
      </div>

      <DataTablePagination
        page={page}
        pageCount={pageCount}
        setPage={(newPage) => handleSetUrlParam("page", newPage.toString())}
        canPreviousPage={page > 1}
        canNextPage={page < pageCount}
        isFetching={isFetching}
      />
    </div>
  );
}
