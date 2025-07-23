"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { queryKeys } from "@/constants/queryKeys";
import {
  createAdminSubSection,
  updateAdminSubSection,
  getAdminAllSections,
} from "@/services/api/admin/learning.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { AdminSubSection } from "@/types/api/admin/learning.types";

// The form schema now includes the required `section_id`.
const formSchema = z.object({
  name: z.string().min(3, "Name must be at least 3 characters."),
  section_id: z.coerce.number({
    required_error: "A parent section is required.",
  }),
  description: z.string().optional(),
  order: z.coerce.number().int().optional(),
});

type SubsectionFormValues = z.infer<typeof formSchema>;
export type SubsectionWithParentId = AdminSubSection & { section_id: number };

interface SubsectionFormDialogProps {
  isOpen: boolean;
  onClose: () => void;
  subsectionId: number | null;
  // Use the new, more accurate type for the initialData prop
  initialData?: SubsectionWithParentId | null;
}

export function SubsectionFormDialog({
  isOpen,
  onClose,
  subsectionId,
  initialData,
}: SubsectionFormDialogProps) {
  const queryClient = useQueryClient();
  const isEditMode = subsectionId !== null;

  // Query to get all sections for the dropdown menu.
  const { data: sectionsData, isLoading: isLoadingSections } = useQuery({
    queryKey: queryKeys.admin.learning.sections.list({ all: true }),
    queryFn: () => getAdminAllSections(),
    enabled: isOpen,
  });

  const form = useForm<SubsectionFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: "", description: "", order: 0 },
  });

  useEffect(() => {
    if (isEditMode && initialData) {
      form.reset({
        name: initialData.name,
        description: initialData.description || "",
        order: initialData.order,
        section_id: initialData.section_id,
      });
    } else {
      form.reset({ name: "", description: "", order: 0 });
    }
  }, [isOpen, isEditMode, initialData, form]);

  const mutation = useMutation({
    mutationFn: (values: SubsectionFormValues) =>
      isEditMode
        ? updateAdminSubSection(subsectionId!, values)
        : createAdminSubSection(values),
    onSuccess: () => {
      toast.success(
        `Subsection ${isEditMode ? "updated" : "created"} successfully!`
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.subsections.lists(),
      });
      onClose();
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, "Failed to save subsection.")),
  });

  const onSubmit = (values: SubsectionFormValues) => mutation.mutate(values);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "Edit Subsection" : "Create New Subsection"}
          </DialogTitle>
          <DialogDescription>
            Fill in the details. A parent section is required.
          </DialogDescription>
        </DialogHeader>
        {isLoadingSections ? (
          <div className="space-y-4 py-4">
            <Skeleton className="h-32 w-full" />
          </div>
        ) : (
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4 pt-4"
            >
              <FormField
                control={form.control}
                name="section_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Parent Section *</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value?.toString()}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a parent section" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {sectionsData?.results.map((section) => (
                          <SelectItem
                            key={section.id}
                            value={section.id.toString()}
                          >
                            {section.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name *</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="order"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Order</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        value={field.value ?? 0}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button type="button" variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending ? "Saving..." : "Save"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        )}
      </DialogContent>
    </Dialog>
  );
}
