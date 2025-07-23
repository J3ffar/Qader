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
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { queryKeys } from "@/constants/queryKeys";
// Make sure getAdminSections is imported
import {
  createAdminSection,
  updateAdminSection,
  getAdminSections,
} from "@/services/api/admin/learning.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

const formSchema = z.object({
  name: z.string().min(3, "Name must be at least 3 characters."),
  description: z.string().optional(),
  order: z.coerce.number().int().optional(),
});

type SectionFormValues = z.infer<typeof formSchema>;

interface SectionFormDialogProps {
  isOpen: boolean;
  onClose: () => void;
  sectionId: number | null;
}

export function SectionFormDialog({
  isOpen,
  onClose,
  sectionId,
}: SectionFormDialogProps) {
  const queryClient = useQueryClient();
  const isEditMode = sectionId !== null;

  // **THE FIX IS HERE**
  const { data: sectionData, isLoading } = useQuery({
    // The queryKey remains the same, targeting the list
    queryKey: queryKeys.admin.learning.sections.list({ all: true }), // Use a key for all items to avoid pagination issues

    // We add the queryFn to tell React Query how to fetch if data is not cached
    queryFn: () => getAdminSections({ page_size: 1000 }), // Fetch all sections

    // The select function still works perfectly to find the specific item
    select: (data) => data?.results.find((s) => s.id === sectionId),

    // The enabled flag ensures this query only runs when needed
    enabled: isEditMode && isOpen,
  });

  const form = useForm<SectionFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: "", description: "", order: 0 },
  });

  useEffect(() => {
    if (isEditMode && sectionData) {
      form.reset({
        name: sectionData.name,
        description: sectionData.description || "",
        order: sectionData.order,
      });
    } else if (!isEditMode) {
      // Ensure form is cleared for create mode
      form.reset({ name: "", description: "", order: 0 });
    }
  }, [isOpen, isEditMode, sectionData, form]);

  const mutation = useMutation({
    mutationFn: (values: SectionFormValues) =>
      isEditMode
        ? updateAdminSection(sectionId!, values)
        : createAdminSection(values),
    onSuccess: () => {
      toast.success(
        `Section ${isEditMode ? "updated" : "created"} successfully!`
      );
      // Invalidate all section list queries to ensure all views are updated
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.sections.lists(),
      });
      onClose();
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, "Failed to save section.")),
  });

  const onSubmit = (values: SectionFormValues) => mutation.mutate(values);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "Edit Section" : "Create New Section"}
          </DialogTitle>
          <DialogDescription>
            Fill in the details for the learning section.
          </DialogDescription>
        </DialogHeader>
        {isEditMode && isLoading ? ( // Show skeleton only in edit mode while loading
          <div className="space-y-4 py-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : (
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4 pt-4"
            >
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
