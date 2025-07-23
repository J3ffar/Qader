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
  createAdminSkill,
  updateAdminSkill,
  getAdminAllSubSections,
} from "@/services/api/admin/learning.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { AdminSkill } from "@/types/api/admin/learning.types";

const formSchema = z.object({
  name: z.string().min(3, "Name must be at least 3 characters."),
  subsection_id: z.coerce.number({
    required_error: "A parent subsection is required.",
  }),
  description: z.string().optional(),
});

type SkillFormValues = z.infer<typeof formSchema>;
export type SkillWithParentId = AdminSkill & { subsection_id: number };

interface SkillFormDialogProps {
  isOpen: boolean;
  onClose: () => void;
  skillId: number | null;
  initialData?: SkillWithParentId | null;
}

export function SkillFormDialog({
  isOpen,
  onClose,
  skillId,
  initialData,
}: SkillFormDialogProps) {
  const queryClient = useQueryClient();
  const isEditMode = skillId !== null;

  const { data: subsectionsData, isLoading: isLoadingSubsections } = useQuery({
    queryKey: queryKeys.admin.learning.subsections.list({ all: true }),
    queryFn: () => getAdminAllSubSections(),
    enabled: isOpen,
  });

  const form = useForm<SkillFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: "", description: "" },
  });

  useEffect(() => {
    if (isEditMode && initialData) {
      form.reset({
        name: initialData.name,
        description: initialData.description || "",
        subsection_id: initialData.subsection_id,
      });
    } else {
      form.reset({ name: "", description: "" });
    }
  }, [isOpen, isEditMode, initialData, form]);

  const mutation = useMutation({
    mutationFn: (values: SkillFormValues) =>
      isEditMode
        ? updateAdminSkill(skillId!, values)
        : createAdminSkill(values),
    onSuccess: () => {
      toast.success(
        `Skill ${isEditMode ? "updated" : "created"} successfully!`
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.skills.lists(),
      });
      onClose();
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, "Failed to save skill.")),
  });

  const onSubmit = (values: SkillFormValues) => mutation.mutate(values);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "Edit Skill" : "Create New Skill"}
          </DialogTitle>
          <DialogDescription>
            Fill in the details. A parent subsection is required.
          </DialogDescription>
        </DialogHeader>
        {isLoadingSubsections ? (
          <div className="space-y-4 py-4">
            <Skeleton className="h-24 w-full" />
          </div>
        ) : (
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4 pt-4"
            >
              <FormField
                control={form.control}
                name="subsection_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Parent Subsection *</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value?.toString()}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a parent subsection" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {subsectionsData?.results.map((sub) => (
                          <SelectItem key={sub.id} value={sub.id.toString()}>
                            {sub.name} ({sub.section_name})
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
