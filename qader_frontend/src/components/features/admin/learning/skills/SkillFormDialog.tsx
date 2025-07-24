"use client";

import { useEffect, useState } from "react";
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
  getAdminAllSections,
} from "@/services/api/admin/learning.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { AdminSkill } from "@/types/api/admin/learning.types";

const formSchema = z.object({
  name: z.string().min(3, "يجب ألا يقل الاسم عن 3 أحرف."),
  subsection_id: z.coerce.number({
    required_error: "يجب اختيار القسم الفرعي.",
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

  const [selectedSection, setSelectedSection] = useState<number | undefined>();

  const form = useForm<SkillFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: "", description: "" },
  });

  const { data: sectionsData, isLoading: isLoadingSections } = useQuery({
    queryKey: queryKeys.admin.learning.sections.list({ all: true }),
    queryFn: getAdminAllSections,
    enabled: isOpen,
  });

  const { data: allSubsectionsData } = useQuery({
    queryKey: queryKeys.admin.learning.subsections.list({ all: true }),
    queryFn: () => getAdminAllSubSections(),
    enabled: isOpen && isEditMode && !!initialData,
  });

  const { data: filteredSubsectionsData, isLoading: isLoadingSubsections } =
    useQuery({
      queryKey: queryKeys.admin.learning.subsections.list({
        sectionId: selectedSection,
      }),
      queryFn: () => getAdminAllSubSections(selectedSection),
      enabled: isOpen && !!selectedSection,
    });

  useEffect(() => {
    // This effect now correctly populates the form in edit mode
    if (
      isOpen &&
      isEditMode &&
      initialData &&
      allSubsectionsData &&
      sectionsData
    ) {
      // THE FIX IS HERE: Find the section_id by linking subsection and section data
      const parentSub = allSubsectionsData.results.find(
        (s) => s.id === initialData.subsection_id
      );

      if (parentSub) {
        const parentSection = sectionsData.results.find(
          (sec) => sec.name === parentSub.section_name
        );
        if (parentSection) {
          setSelectedSection(parentSection.id);
        }
      }

      form.reset({
        name: initialData.name,
        description: initialData.description || "",
        subsection_id: initialData.subsection_id,
      });
    } else if (!isEditMode) {
      form.reset({ name: "", description: "" });
      setSelectedSection(undefined);
    }
    // Added dependencies to ensure the effect runs when all data is ready
  }, [isOpen, isEditMode, initialData, form, allSubsectionsData, sectionsData]);

  const mutation = useMutation({
    mutationFn: (values: SkillFormValues) =>
      isEditMode
        ? updateAdminSkill(skillId!, values)
        : createAdminSkill(values),
    onSuccess: () => {
      toast.success(`تم ${isEditMode ? "تحديث" : "إنشاء"} المهارة بنجاح!`);
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.skills.lists(),
      });
      onClose();
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, "فشل حفظ المهارة.")),
  });

  const onSubmit = (values: SkillFormValues) => mutation.mutate(values);
  const handleClose = () => {
    onClose();
    form.reset();
    setSelectedSection(undefined);
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "تعديل المهارة" : "إنشاء مهارة جديدة"}
          </DialogTitle>
          <DialogDescription>
            املأ التفاصيل. يجب اختيار قسم رئيسي وقسم فرعي.
          </DialogDescription>
        </DialogHeader>
        {isLoadingSections ? (
          <div className="space-y-4 py-4">
            <Skeleton className="h-24 w-full" />
          </div>
        ) : (
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4 pt-4"
            >
              <FormItem>
                <FormLabel>القسم الرئيسي *</FormLabel>
                <Select
                  onValueChange={(v) => {
                    setSelectedSection(Number(v));
                    form.resetField("subsection_id");
                  }}
                  value={selectedSection?.toString()}
                  dir="rtl"
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="اختر القسم الرئيسي أولاً" />
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
              </FormItem>

              <FormField
                control={form.control}
                name="subsection_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>القسم الفرعي *</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value?.toString()}
                      disabled={!selectedSection || isLoadingSubsections}
                      dir="rtl"
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="اختر القسم الفرعي" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {filteredSubsectionsData?.results.map((sub) => (
                          <SelectItem key={sub.id} value={sub.id.toString()}>
                            {sub.name}
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
                    <FormLabel>اسم المهارة *</FormLabel>
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
              <DialogFooter>
                <Button type="button" variant="outline" onClick={handleClose}>
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
