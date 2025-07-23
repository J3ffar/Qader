"use client";

import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/shared/DataTable";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { DeleteConfirmationDialog } from "@/components/shared/DeleteConfirmationDialog";
import { queryKeys } from "@/constants/queryKeys";
import {
  getAdminSkills,
  deleteAdminSkill,
  getAdminAllSubSections,
} from "@/services/api/admin/learning.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { getColumns } from "./columns";
import { SkillFormDialog, SkillWithParentId } from "./SkillFormDialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AdminSkill } from "@/types/api/admin/learning.types";

const ITEMS_PER_PAGE = 20;

export function SkillsClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<
    AdminSkill | SkillWithParentId | null
  >(null);

  const filters = useMemo(
    () => ({
      page: searchParams.get("page") ?? "1",
      subsection__id: searchParams.get("subsection") ?? "",
      ordering: searchParams.get("ordering") ?? "",
    }),
    [searchParams]
  );

  const handleSetUrlParams = (newParams: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(newParams).forEach(([key, value]) =>
      value ? params.set(key, value) : params.delete(key)
    );
    if (!("page" in newParams)) params.set("page", "1");
    router.replace(`${pathname}?${params.toString()}`);
  };

  const { data: subsections } = useQuery({
    queryKey: queryKeys.admin.learning.subsections.list({ all: true }),
    queryFn: () => getAdminAllSubSections(),
  });
  const { data, isLoading, isFetching, isError, error } = useQuery({
    queryKey: queryKeys.admin.learning.skills.list(filters),
    queryFn: () => getAdminSkills(filters),
    placeholderData: (prev) => prev,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteAdminSkill(id),
    onSuccess: () => {
      toast.success("Skill deleted successfully.");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.skills.lists(),
      });
      handleCloseDialogs();
    },
    onError: (err) =>
      toast.error(getApiErrorMessage(err, "Failed to delete skill.")),
  });

  const handleEdit = (id: number) => {
    const itemToEdit = data?.results.find((s) => s.id === id);
    if (itemToEdit) {
      const parentSub = subsections?.results.find(
        (s) => s.name === itemToEdit.subsection_name
      );
      if (parentSub) {
        const itemWithParentId: SkillWithParentId = {
          ...itemToEdit,
          subsection_id: parentSub.id,
        };
        setSelectedItem(itemWithParentId);
        setIsFormOpen(true);
      } else {
        toast.error("Could not find parent subsection data for this item.");
      }
    }
  };
  const handleDelete = (id: number) => {
    const itemToDelete = data?.results.find((s) => s.id === id);
    if (itemToDelete) {
      setSelectedItem(itemToDelete);
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

  const columns = useMemo(() => getColumns(), []);
  const pageCount = data?.count ? Math.ceil(data.count / ITEMS_PER_PAGE) : 0;
  const currentPage = parseInt(filters.page?.toString() ?? "1", 10);

  if (isError) return <div>Error: {error.message}</div>;

  return (
    <div className="space-y-4">
      <SkillFormDialog
        isOpen={isFormOpen}
        onClose={handleCloseDialogs}
        skillId={selectedItem?.id || null}
        initialData={selectedItem as SkillWithParentId | null}
      />
      <DeleteConfirmationDialog
        isOpen={isDeleteOpen}
        onClose={handleCloseDialogs}
        onConfirm={handleDeleteConfirm}
        isPending={deleteMutation.isPending}
        itemType="skill"
      />

      <div className="flex items-center justify-between gap-2">
        <h2 className="text-2xl font-bold tracking-tight">Skills</h2>
        <div className="flex items-center gap-2">
          <Select
            value={filters.subsection__id}
            onValueChange={(val) => handleSetUrlParams({ subsection: val })}
          >
            <SelectTrigger className="w-[240px]">
              <SelectValue placeholder="Filter by Subsection..." />
            </SelectTrigger>
            <SelectContent>
              {subsections?.results.map((s) => (
                <SelectItem key={s.id} value={s.id.toString()}>
                  {s.name} ({s.section_name})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {filters.subsection__id && (
            <Button
              variant="ghost"
              onClick={() => handleSetUrlParams({ subsection: null })}
            >
              Clear
            </Button>
          )}
          <Button
            onClick={() => {
              setSelectedItem(null);
              setIsFormOpen(true);
            }}
          >
            Add Skill
          </Button>
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
