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

const formSchema = z.object({
  name: z.string().min(3, "يجب ألا يقل الاسم عن 3 أحرف."),
  section_id: z.coerce.number({
    required_error: "يجب اختيار القسم الرئيسي.",
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
      toast.success(`تم ${isEditMode ? "تحديث" : "إنشاء"} القسم الفرعي بنجاح!`);
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.subsections.lists(),
      });
      onClose();
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, "فشل حفظ القسم الفرعي.")),
  });

  const onSubmit = (values: SubsectionFormValues) => mutation.mutate(values);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "تعديل القسم الفرعي" : "إنشاء قسم فرعي جديد"}
          </DialogTitle>
          <DialogDescription>
            املأ التفاصيل. اختيار القسم الرئيسي إلزامي.
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
                    <FormLabel>القسم الرئيسي *</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value?.toString()}
                      dir="rtl"
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="اختر القسم الرئيسي" />
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
