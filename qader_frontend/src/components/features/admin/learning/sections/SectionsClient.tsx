"use client";

import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/shared/DataTable";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { queryKeys } from "@/constants/queryKeys";
import {
  getAdminSections,
  deleteAdminSection,
} from "@/services/api/admin/learning.service";
import { getColumns } from "./columns";
import { SectionFormDialog } from "./SectionFormDialog";
import { DeleteConfirmationDialog } from "@/components/shared/DeleteConfirmationDialog";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

const ITEMS_PER_PAGE = 10;

export function SectionsClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  // Dialog states
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedSectionId, setSelectedSectionId] = useState<number | null>(
    null
  );

  const filters = useMemo(
    () => ({
      page: searchParams.get("page") ?? "1",
      search: searchParams.get("search") ?? "",
      ordering: searchParams.get("ordering") ?? "",
    }),
    [searchParams]
  );

  const { data, isLoading, isFetching, isError, error } = useQuery({
    queryKey: queryKeys.admin.learning.sections.list(filters),
    queryFn: () => getAdminSections(filters),
    placeholderData: (prev) => prev,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteAdminSection(id),
    onSuccess: () => {
      toast.success("تم حذف القسم بنجاح.");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.sections.lists(),
      });
      handleCloseDialogs();
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "فشل حذف القسم."));
    },
  });

  const handleEdit = (id: number) => {
    setSelectedSectionId(id);
    setIsFormOpen(true);
  };
  const handleDelete = (id: number) => {
    setSelectedSectionId(id);
    setIsDeleteOpen(true);
  };

  const handleCloseDialogs = () => {
    setIsFormOpen(false);
    setIsDeleteOpen(false);
    setSelectedSectionId(null);
  };

  const handleDeleteConfirm = () => {
    if (selectedSectionId) {
      deleteMutation.mutate(selectedSectionId);
    }
  };

  const columns = useMemo(() => getColumns(), []);
  const pageCount = data?.count ? Math.ceil(data.count / ITEMS_PER_PAGE) : 0;
  const currentPage = parseInt(filters.page?.toString() ?? "1", 10);

  if (isError) return <div>خطأ: {error.message}</div>;

  const handleSetUrlParams = (newParams: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(newParams).forEach(([key, value]) => {
      if (value) params.set(key, value);
      else params.delete(key);
    });
    if (!("page" in newParams)) {
      params.set("page", "1");
    }
    router.replace(`${pathname}?${params.toString()}`);
  };

  return (
    <div className="space-y-4">
      <SectionFormDialog
        isOpen={isFormOpen}
        onClose={handleCloseDialogs}
        sectionId={selectedSectionId}
      />
      <DeleteConfirmationDialog
        isOpen={isDeleteOpen}
        onClose={handleCloseDialogs}
        onConfirm={handleDeleteConfirm}
        isPending={deleteMutation.isPending}
        itemType="القسم" // Translated
      />

      <div className="flex items-center justify-between gap-2">
        <h2 className="text-2xl font-bold tracking-tight">الأقسام الرئيسية</h2>
        <Button
          onClick={() => {
            setSelectedSectionId(null);
            setIsFormOpen(true);
          }}
        >
          إضافة قسم
        </Button>
      </div>

      <div className="rounded-md border">
        <DataTable
          columns={columns}
          data={data?.results ?? []}
          isLoading={isLoading}
          context={{ handleEdit, handleDelete }}
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
