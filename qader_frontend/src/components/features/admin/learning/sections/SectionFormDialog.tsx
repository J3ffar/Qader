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
import {
  createAdminSection,
  updateAdminSection,
  getAdminSections,
} from "@/services/api/admin/learning.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

const formSchema = z.object({
  name: z.string().min(3, "يجب ألا يقل الاسم عن 3 أحرف."),
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

  const { data: sectionData, isLoading } = useQuery({
    queryKey: queryKeys.admin.learning.sections.list({ all: true }),
    queryFn: () => getAdminSections({ page_size: 1000 }),
    select: (data) => data?.results.find((s) => s.id === sectionId),
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
      form.reset({ name: "", description: "", order: 0 });
    }
  }, [isOpen, isEditMode, sectionData, form]);

  const mutation = useMutation({
    mutationFn: (values: SectionFormValues) =>
      isEditMode
        ? updateAdminSection(sectionId!, values)
        : createAdminSection(values),
    onSuccess: () => {
      toast.success(`تم ${isEditMode ? "تحديث" : "إنشاء"} القسم بنجاح!`);
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.sections.lists(),
      });
      onClose();
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, "فشل حفظ القسم.")),
  });

  const onSubmit = (values: SectionFormValues) => mutation.mutate(values);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "تعديل القسم" : "إنشاء قسم جديد"}
          </DialogTitle>
          <DialogDescription>املأ تفاصيل القسم التعليمي.</DialogDescription>
        </DialogHeader>
        {isEditMode && isLoading ? (
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
                    <FormLabel>الاسم *</FormLabel>
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
                    <FormLabel>الوصف</FormLabel>
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
                    <FormLabel>الترتيب</FormLabel>
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
                  إلغاء
                </Button>
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending ? "جاري الحفظ..." : "حفظ"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        )}
      </DialogContent>
    </Dialog>
  );
}
