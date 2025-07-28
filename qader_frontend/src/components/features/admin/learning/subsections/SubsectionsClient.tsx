"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/shared/DataTable";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { DeleteConfirmationDialog } from "@/components/shared/DeleteConfirmationDialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { X } from "lucide-react";
import { queryKeys } from "@/constants/queryKeys";
import {
  getAdminSubSections,
  deleteAdminSubSection,
  getAdminAllSections,
} from "@/services/api/admin/learning.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { getColumns } from "./columns";
import {
  SubsectionFormDialog,
  SubsectionWithParentId,
} from "./SubsectionFormDialog";
import { AdminSubSection } from "@/types/api/admin/learning.types";
import { useDebounce } from "@/hooks/use-debounce";

const ITEMS_PER_PAGE = 20;

export function SubsectionsClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<AdminSubSection | null>(
    null
  );

  // Read all filters from URL
  const filters = useMemo(
    () => ({
      page: searchParams.get("page") ?? "1",
      section__id: searchParams.get("section") ?? "",
      search: searchParams.get("search") ?? "", // Added search to filters
      ordering: searchParams.get("ordering") ?? "-created_at",
    }),
    [searchParams]
  );

  // Local state for search input to allow debouncing
  const [searchValue, setSearchValue] = useState(filters.search);
  const debouncedSearch = useDebounce(searchValue, 500);

  useEffect(() => {
    // Only update URL if debounced value differs from URL state
    if (debouncedSearch !== filters.search) {
      handleSetUrlParams({ search: debouncedSearch || null });
    }
  }, [debouncedSearch]);

  const handleSetUrlParams = (newParams: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(newParams).forEach(([key, value]) =>
      value ? params.set(key, value) : params.delete(key)
    );
    if (!("page" in newParams)) params.set("page", "1");
    router.replace(`${pathname}?${params.toString()}`);
  };

  const { data: sections } = useQuery({
    queryKey: queryKeys.admin.learning.sections.list({ all: true }),
    queryFn: () => getAdminAllSections(),
  });
  const { data, isLoading, isFetching, isError, error } = useQuery({
    queryKey: queryKeys.admin.learning.subsections.list(filters),
    queryFn: () => getAdminSubSections(filters),
    placeholderData: (prev) => prev,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteAdminSubSection(id),
    onSuccess: () => {
      toast.success("تم حذف القسم الفرعي بنجاح.");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.subsections.lists(),
      });
      handleCloseDialogs();
    },
    onError: (err) =>
      toast.error(getApiErrorMessage(err, "فشل حذف القسم الفرعي.")),
  });

  const handleEdit = (id: number) => {
    const itemToEdit = data?.results.find((s) => s.id === id);
    if (itemToEdit) {
      const parentSection = sections?.results.find(
        (s) => s.name === itemToEdit.section_name
      );
      if (parentSection) {
        const itemWithParentId: SubsectionWithParentId = {
          ...itemToEdit,
          section_id: parentSection.id,
        };
        setSelectedItem(itemWithParentId);
        setIsFormOpen(true);
      } else {
        toast.error("بيانات القسم الرئيسي غير متوفرة. لا يمكن التعديل.");
      }
    }
  };
  const handleDelete = (id: number) => {
    const item = data?.results.find((s) => s.id === id);
    if (item) {
      setSelectedItem(item);
      setIsDeleteOpen(true);
    }
  };
  const handleCloseDialogs = () => {
    setIsFormOpen(false);
    setIsDeleteOpen(false);
    setSelectedItem(null);
  };
  const handleDeleteConfirm = () => {
    if (selectedItem) deleteMutation.mutate(selectedItem.id);
  };

  const handleClearFilters = () => {
    setSearchValue("");
    handleSetUrlParams({ section: null, search: null });
  };
  const isFiltered = !!filters.section__id || !!filters.search;

  const columns = useMemo(() => getColumns(), []);
  const pageCount = data?.count ? Math.ceil(data.count / ITEMS_PER_PAGE) : 0;
  const currentPage = parseInt(filters.page?.toString() ?? "1", 10);

  if (isError) return <div>خطأ: {error.message}</div>;

  return (
    <div className="space-y-4">
      <SubsectionFormDialog
        isOpen={isFormOpen}
        onClose={handleCloseDialogs}
        subsectionId={selectedItem?.id || null}
        initialData={selectedItem as SubsectionWithParentId | null}
      />
      <DeleteConfirmationDialog
        isOpen={isDeleteOpen}
        onClose={handleCloseDialogs}
        onConfirm={handleDeleteConfirm}
        isPending={deleteMutation.isPending}
        itemType="القسم الفرعي"
      />

      <div className="flex items-center justify-between gap-2 flex-wrap">
        <h2 className="text-2xl font-bold tracking-tight">الأقسام الفرعية</h2>
        <Button
          onClick={() => {
            setSelectedItem(null);
            setIsFormOpen(true);
          }}
        >
          إضافة قسم فرعي
        </Button>
      </div>

      {/* Filters Toolbar */}
      <div className="p-4 border rounded-md">
        <div className="flex items-center gap-2 flex-wrap">
          <Input
            placeholder="ابحث بالاسم أو الوصف..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            className="max-w-xs"
          />
          <Select
            value={filters.section__id}
            onValueChange={(val) =>
              handleSetUrlParams({ section: val || null })
            }
            dir="rtl"
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="التصفية حسب القسم" />
            </SelectTrigger>
            <SelectContent>
              {sections?.results.map((s) => (
                <SelectItem key={s.id} value={s.id.toString()}>
                  {s.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {isFiltered && (
            <Button variant="ghost" onClick={handleClearFilters}>
              <X className="rtl:ml-2 ltr:mr-2 h-4 w-4" />
              مسح الفلاتر
            </Button>
          )}
        </div>
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
