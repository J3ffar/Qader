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
import { Switch } from "@/components/ui/switch";
import { queryKeys } from "@/constants/queryKeys";
import {
  getAdminQuestionDetail,
  createAdminQuestion,
  updateAdminQuestion,
  getAdminAllSections,
  getAdminAllSubSections,
  getAdminAllSkills,
} from "@/services/api/admin/learning.service";
import { AdminQuestionCreateUpdate } from "@/types/api/admin/learning.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Skeleton } from "@/components/ui/skeleton";

const difficultyLevels = [
  { value: 1, label: "1 - سهل جداً" },
  { value: 2, label: "2 - سهل" },
  { value: 3, label: "3 - متوسط" },
  { value: 4, label: "4 - صعب" },
  { value: 5, label: "5 - صعب جداً" },
];

const answerOptions = ["A", "B", "C", "D"] as const;

const formSchema = z.object({
  question_text: z.string().min(10, "يجب أن لا يقل نص السؤال عن 10 أحرف."),
  option_a: z.string().min(1, "الخيار أ مطلوب."),
  option_b: z.string().min(1, "الخيار ب مطلوب."),
  option_c: z.string().min(1, "الخيار ج مطلوب."),
  option_d: z.string().min(1, "الخيار د مطلوب."),
  correct_answer: z.enum(answerOptions, {
    required_error: "الإجابة الصحيحة مطلوبة.",
  }),
  difficulty: z.coerce.number().min(1).max(5),
  section_id: z.coerce.number({ required_error: "القسم الرئيسي مطلوب." }),
  subsection_id: z.coerce.number({ required_error: "القسم الفرعي مطلوب." }),
  skill_id: z.coerce.number().nullable().optional(),
  is_active: z.boolean(),
  image_upload: z.any().optional(),
  explanation: z.string().optional().nullable(),
  hint: z.string().optional().nullable(),
  solution_method_summary: z.string().optional().nullable(),
});

type QuestionFormValues = z.infer<typeof formSchema>;

const defaultFormValues: Partial<QuestionFormValues> = {
  question_text: "",
  option_a: "",
  option_b: "",
  option_c: "",
  option_d: "",
  is_active: true,
  difficulty: 3,
  explanation: "",
  hint: "",
  solution_method_summary: "",
};
interface QuestionFormDialogProps {
  isOpen: boolean;
  onClose: () => void;
  questionId: number | null;
}

export function QuestionFormDialog({
  isOpen,
  onClose,
  questionId,
}: QuestionFormDialogProps) {
  const queryClient = useQueryClient();
  const [selectedSection, setSelectedSection] = useState<number | undefined>(
    undefined
  );
  const [selectedSubsection, setSelectedSubsection] = useState<
    number | undefined
  >(undefined);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  const isEditMode = questionId !== null;

  const {
    data: question,
    isLoading: isLoadingQuestion,
    isSuccess: isQuestionLoaded,
  } = useQuery({
    queryKey: queryKeys.admin.learning.questions.detail(questionId!),
    queryFn: () => getAdminQuestionDetail(questionId!),
    enabled: isEditMode && isOpen,
  });

  const { data: sections } = useQuery({
    queryKey: queryKeys.admin.learning.sections.list({ all: true }),
    queryFn: getAdminAllSections,
    enabled: !isLoadingQuestion && isOpen,
  });

  const { data: subsections } = useQuery({
    queryKey: queryKeys.admin.learning.subsections.list({
      sectionId: selectedSection,
    }),
    queryFn: () => getAdminAllSubSections(selectedSection!),
    enabled: typeof selectedSection === "number" && isOpen,
  });
  const { data: skills } = useQuery({
    queryKey: queryKeys.admin.learning.skills.list({
      subsectionId: selectedSubsection,
    }),
    queryFn: () => getAdminAllSkills(selectedSubsection!),
    enabled: typeof selectedSubsection === "number" && isOpen,
  });

  const form = useForm<QuestionFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: defaultFormValues,
  });

  useEffect(() => {
    if (isEditMode && isQuestionLoaded && question) {
      form.reset({
        question_text: question.question_text,
        option_a: question.options.A,
        option_b: question.options.B,
        option_c: question.options.C,
        option_d: question.options.D,
        correct_answer: question.correct_answer,
        difficulty: question.difficulty,
        section_id: question.section.id,
        subsection_id: question.subsection.id,
        skill_id: question.skill?.id || null,
        is_active: question.is_active,
        explanation: question.explanation,
        hint: question.hint,
        solution_method_summary: question.solution_method_summary,
        image_upload: null,
      });
      setSelectedSection(question.section.id);
      setSelectedSubsection(question.subsection.id);
      setImagePreview(question.image);
    } else if (!isEditMode) {
      form.reset(defaultFormValues);
      setSelectedSection(undefined);
      setSelectedSubsection(undefined);
      setImagePreview(null);
    }
  }, [isEditMode, isQuestionLoaded, question, form]);

  const mutation = useMutation({
    mutationFn: (values: QuestionFormValues) => {
      let payload: Partial<AdminQuestionCreateUpdate> & { image?: null } = {
        ...values,
      };
      if (payload.image_upload === undefined) {
        payload.image_upload = null;
      }
      return isEditMode
        ? updateAdminQuestion(questionId, payload)
        : createAdminQuestion(payload as AdminQuestionCreateUpdate);
    },
    onSuccess: () => {
      toast.success(`تم ${isEditMode ? "تحديث" : "إنشاء"} السؤال بنجاح!`);
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.questions.lists(),
      });
      if (isEditMode) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.admin.learning.questions.detail(questionId),
        });
      }
      handleClose();
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "فشل حفظ السؤال."));
    },
  });

  const onSubmit = (values: QuestionFormValues) => mutation.mutate(values);
  const handleClose = () => {
    form.reset();
    onClose();
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImagePreview(URL.createObjectURL(file));
      form.setValue("image_upload", file);
    }
  };

  const handleRemoveImage = () => {
    setImagePreview(null);
    form.setValue("image_upload", null);
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "تعديل السؤال" : "إنشاء سؤال جديد"}
          </DialogTitle>
          <DialogDescription>
            املأ التفاصيل أدناه. جميع الحقول التي تحتوي على علامة (*) مطلوبة.
          </DialogDescription>
        </DialogHeader>
        {isEditMode && isLoadingQuestion ? (
          <div className="space-y-4 py-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : (
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-6 pt-4"
            >
              {/* Form content with translated labels, placeholders etc. */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-6">
                  {/* Hierarchy Selects */}
                  <FormField
                    control={form.control}
                    name="section_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>القسم الرئيسي *</FormLabel>
                        <Select
                          onValueChange={(v) => {
                            field.onChange(v);
                            setSelectedSection(Number(v));
                            form.setValue("subsection_id", undefined as any);
                            form.setValue("skill_id", undefined);
                            setSelectedSubsection(undefined);
                          }}
                          value={field.value?.toString()}
                          dir="rtl"
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="اختر قسمًا رئيسيًا" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {sections?.results.map((s) => (
                              <SelectItem key={s.id} value={s.id.toString()}>
                                {s.name}
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
                    name="subsection_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>القسم الفرعي *</FormLabel>
                        <Select
                          onValueChange={(v) => {
                            field.onChange(v);
                            setSelectedSubsection(Number(v));
                            form.setValue("skill_id", undefined);
                          }}
                          value={field.value?.toString()}
                          disabled={!selectedSection}
                          dir="rtl"
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="اختر قسمًا فرعيًا" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {subsections?.results.map((s) => (
                              <SelectItem key={s.id} value={s.id.toString()}>
                                {s.name}
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
                    name="skill_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>المهارة (اختياري)</FormLabel>
                        <Select
                          onValueChange={field.onChange}
                          value={field.value?.toString()}
                          dir="rtl"
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="اختر مهارة" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {skills?.results.map((s) => (
                              <SelectItem key={s.id} value={s.id.toString()}>
                                {s.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Image Upload */}
                  <FormField
                    control={form.control}
                    name="image_upload"
                    render={() => (
                      <FormItem>
                        <FormLabel>الصورة (اختياري)</FormLabel>
                        {imagePreview && (
                          <div className="mt-2">
                            <img
                              src={imagePreview}
                              alt="معاينة"
                              className="max-h-40 rounded-md"
                            />
                          </div>
                        )}
                        <FormControl>
                          <Input
                            type="file"
                            accept="image/*"
                            onChange={handleImageChange}
                          />
                        </FormControl>
                        {isEditMode && imagePreview && (
                          <Button
                            type="button"
                            variant="link"
                            size="sm"
                            className="p-0 h-auto"
                            onClick={handleRemoveImage}
                          >
                            إزالة الصورة
                          </Button>
                        )}
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="space-y-6">
                  {/* Question and Options */}
                  <FormField
                    control={form.control}
                    name="question_text"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>نص السؤال *</FormLabel>
                        <FormControl>
                          <Textarea {...field} rows={4} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="option_a"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>الخيار أ *</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="option_b"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>الخيار ب *</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="option_c"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>الخيار ج *</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="option_d"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>الخيار د *</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <FormField
                  control={form.control}
                  name="correct_answer"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>الإجابة الصحيحة *</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                        dir="rtl"
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="اختر الإجابة الصحيحة" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {answerOptions.map((opt) => (
                            <SelectItem key={opt} value={opt}>
                              الخيار {opt}
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
                  name="difficulty"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>مستوى الصعوبة *</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value?.toString()}
                        dir="rtl"
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="اختر مستوى الصعوبة" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {difficultyLevels.map((lvl) => (
                            <SelectItem
                              key={lvl.value}
                              value={lvl.value.toString()}
                            >
                              {lvl.label}
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
                  name="is_active"
                  render={({ field }) => (
                    // RTL adjustment for switch component layout
                    <FormItem className="flex flex-row rtl:flex-row-reverse items-center justify-between rounded-lg border p-3 shadow-sm mt-8">
                      <FormLabel className="rtl:ml-4 ltr:mr-4">نشط</FormLabel>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </div>

              <div className="space-y-6">
                <FormField
                  control={form.control}
                  name="explanation"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>الشرح (اختياري)</FormLabel>
                      <FormControl>
                        <Textarea
                          {...field}
                          value={field.value ?? ""}
                          rows={3}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="hint"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>تلميح (اختياري)</FormLabel>
                      <FormControl>
                        <Textarea {...field} value={field.value ?? ""} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="solution_method_summary"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>ملخص طريقة الحل (اختياري)</FormLabel>
                      <FormControl>
                        <Textarea
                          {...field}
                          value={field.value ?? ""}
                          rows={2}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={handleClose}>
                  إلغاء
                </Button>
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending
                    ? "جاري الحفظ..."
                    : isEditMode
                    ? "حفظ التغييرات"
                    : "إنشاء السؤال"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        )}
      </DialogContent>
    </Dialog>
  );
}
