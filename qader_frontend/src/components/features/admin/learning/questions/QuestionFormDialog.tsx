"use client";

import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, UseFormReturn } from "react-hook-form";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { queryKeys } from "@/constants/queryKeys";
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  getAdminQuestionDetail,
  createAdminQuestion,
  updateAdminQuestion,
  getAdminAllSections,
  getAdminAllSubSections,
  getAdminAllSkills,
  objectToFormData,
} from "@/services/api/admin/learning.service";
import {
  AdminQuestion,
  AdminSectionsListResponse,
  AdminSubSectionsListResponse,
  AdminSkillsListResponse,
  AdminQuestionCreateUpdate,
} from "@/types/api/admin/learning.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Circle, Sigma } from "lucide-react";
import { SearchableCombobox } from "@/components/shared/form/SearchableCombobox"; // <--- IMPORT a new component
// import { RichTextEditor } from "@/components/shared/RichTextEditor";
import { EquationTutorialDialog } from "./EquationTutorialDialog";
import * as z from "zod";
import dynamic from "next/dynamic";

const RichTextEditorSkeleton = () => (
  <div className="flex flex-col">
    <Skeleton className="h-10 w-full rounded-b-none rounded-t-md" />
    <Skeleton className="h-20 w-full rounded-b-md rounded-t-none" />
  </div>
);

// Dynamically import the RichTextEditor and disable SSR for it.
// Provide the custom skeleton as the loading component for a better UX.
const RichTextEditor = dynamic(
  () =>
    import("@/components/shared/RichTextEditor").then(
      (mod) => mod.RichTextEditor
    ),
  {
    ssr: false,
    loading: () => <RichTextEditorSkeleton />,
  }
);

const difficultyLevels = [
  { value: 1, label: "1 - سهل جداً" },
  { value: 2, label: "2 - سهل" },
  { value: 3, label: "3 - متوسط" },
  { value: 4, label: "4 - صعب" },
  { value: 5, label: "5 - صعب جداً" },
];
const answerOptions = ["A", "B", "C", "D"] as const;

const arabicOptionMap: { [key: string]: string } = {
  A: "أ",
  B: "ب",
  C: "ج",
  D: "د",
};

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
  section_id: z.coerce.number({ message: "القسم الرئيسي مطلوب." }),
  subsection_id: z.coerce.number({ message: "القسم الفرعي مطلوب." }),
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

function FormSkeleton() {
  return (
    <div className="space-y-6 pt-4">
      <div className="flex w-full space-x-2 rtl:space-x-reverse">
        <Skeleton className="h-10 flex-1" />
        <Skeleton className="h-10 flex-1" />
        <Skeleton className="h-10 flex-1" />
      </div>
      <Card className="mt-6">
        <CardHeader>
          <Skeleton className="h-7 w-48" />
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Skeleton className="h-5 w-24 mb-2" />
            <Skeleton className="h-28 w-full" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Skeleton className="h-5 w-20 mb-2" />
              <Skeleton className="h-10 w-full" />
            </div>
            <div>
              <Skeleton className="h-5 w-20 mb-2" />
              <Skeleton className="h-10 w-full" />
            </div>
            <div>
              <Skeleton className="h-5 w-20 mb-2" />
              <Skeleton className="h-10 w-full" />
            </div>
            <div>
              <Skeleton className="h-5 w-20 mb-2" />
              <Skeleton className="h-10 w-full" />
            </div>
          </div>
          <div>
            <Skeleton className="h-5 w-32 mb-2" />
            <Skeleton className="h-10 w-full" />
          </div>
        </CardContent>
      </Card>
      <div className="flex justify-end items-center pt-6 gap-2">
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-32" />
      </div>
    </div>
  );
}

interface QuestionFormProps {
  form: UseFormReturn<QuestionFormValues>;
  onSubmit: (values: QuestionFormValues) => void;
  handleClose: () => void;
  handleImageChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleRemoveImage: () => void;
  isEditMode: boolean;
  isPending: boolean;
  imagePreview: string | null;
  // All data is passed down as props
  sections: AdminSectionsListResponse;
  subsections?: AdminSubSectionsListResponse;
  skills?: AdminSkillsListResponse;
  // State setters for dependent dropdowns
  setSelectedSection: (id: number | undefined) => void;
  setSelectedSubsection: (id: number | undefined) => void;
  isLoadingSubsections: boolean;
  isLoadingSkills: boolean;
}
const CORE_CONTENT_FIELDS: (keyof QuestionFormValues)[] = [
  "question_text",
  "option_a",
  "option_b",
  "option_c",
  "option_d",
  "correct_answer",
];
const CLASSIFICATION_FIELDS: (keyof QuestionFormValues)[] = [
  "section_id",
  "subsection_id",
  "difficulty",
];
function QuestionFormComponent({
  form,
  onSubmit,
  handleClose,
  handleImageChange,
  handleRemoveImage,
  isEditMode,
  isPending,
  imagePreview,
  sections,
  subsections,
  skills,
  setSelectedSection,
  setSelectedSubsection,
  isLoadingSubsections,
  isLoadingSkills,
}: QuestionFormProps & {
  isLoadingSubsections: boolean;
  isLoadingSkills: boolean;
}) {
  const {
    formState: { errors },
  } = form;

  const hasErrorInTab = (fieldNames: (keyof QuestionFormValues)[]) => {
    return fieldNames.some((field) => Object.keys(errors).includes(field));
  };

  const hasCoreContentError = hasErrorInTab(CORE_CONTENT_FIELDS);
  const hasClassificationError = hasErrorInTab(CLASSIFICATION_FIELDS);

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-6 pt-4"
        encType="multipart/form-data"
      >
        <Tabs defaultValue="content" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="content">
              المحتوى الأساسي
              {hasCoreContentError && (
                <Circle className="h-2 w-2 rtl:mr-2 ltr:ml-2 fill-red-500 text-red-500" />
              )}
            </TabsTrigger>
            <TabsTrigger value="classification">
              التصنيف والإعدادات
              {hasClassificationError && (
                <Circle className="h-2 w-2 rtl:mr-2 ltr:ml-2 fill-red-500 text-red-500" />
              )}
            </TabsTrigger>
            <TabsTrigger value="helpers">معلومات مساعدة</TabsTrigger>
          </TabsList>

          <TabsContent value="content" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>السؤال والخيارات والصورة</CardTitle>
                <div className="flex items-start gap-x-3 rounded-md border bg-muted/50 p-3 text-sm mt-2">
                  <Sigma className="mt-0.5 h-5 w-5 flex-shrink-0 text-muted-foreground" />
                  <div className="flex-grow">
                    <div className="flex justify-between items-center">
                      <h4 className="font-semibold">إضافة معادلة رياضية</h4>
                      <EquationTutorialDialog />
                    </div>
                    <p className="text-muted-foreground">
                      لإدراج معادلة، ضع المؤشر في المكان المطلوب ثم انقر على
                      أيقونة المعادلة{" "}
                      <span className="inline-flex h-5 w-5 items-center justify-center rounded-sm bg-background mx-1 border font-bold">
                        Σ
                      </span>{" "}
                      في شريط الأدوات.
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <FormField
                  control={form.control}
                  name="question_text"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>نص السؤال *</FormLabel>
                      <FormControl>
                        <RichTextEditor
                          value={field.value}
                          onChange={field.onChange}
                          placeholder="اكتب نص السؤال هنا..."
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="option_a"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>الخيار أ *</FormLabel>
                        <FormControl>
                          <RichTextEditor
                            value={field.value}
                            onChange={field.onChange}
                            placeholder="اكتب نص الخيار أ..."
                          />
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
                          <RichTextEditor
                            value={field.value}
                            onChange={field.onChange}
                            placeholder="اكتب نص الخيار ب..."
                          />
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
                          <RichTextEditor
                            value={field.value}
                            onChange={field.onChange}
                            placeholder="اكتب نص الخيار ج..."
                          />
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
                          <RichTextEditor
                            value={field.value}
                            onChange={field.onChange}
                            placeholder="اكتب نص الخيار د..."
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <FormField
                  control={form.control}
                  name="correct_answer"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>الإجابة الصحيحة</FormLabel>
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
                              الخيار {arabicOptionMap[opt]}
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
                  name="image_upload"
                  render={() => (
                    <FormItem>
                      <FormLabel>الصورة (اختياري)</FormLabel>
                      {imagePreview && (
                        <div className="mt-2 relative w-fit">
                          <img
                            src={imagePreview}
                            alt="معاينة"
                            className="max-h-40 rounded-md border"
                          />
                          <Button
                            type="button"
                            variant="destructive"
                            size="icon"
                            className="absolute -top-2 -right-2 h-6 w-6 rounded-full"
                            onClick={handleRemoveImage}
                          >
                            <span className="sr-only">إزالة الصورة</span>×
                          </Button>
                        </div>
                      )}
                      <FormControl>
                        <Input
                          type="file"
                          accept="image/*"
                          onChange={handleImageChange}
                          className="pt-2 file:text-sm file:font-medium"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="classification" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>التصنيف الهرمي والإعدادات الهامة</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* === REPLACED WITH COMBOBOX === */}
                <SearchableCombobox
                  form={form}
                  fieldName="section_id"
                  label="القسم الرئيسي"
                  options={sections?.results || []}
                  placeholder="اختر قسمًا رئيسيًا"
                  searchPlaceholder="ابحث عن قسم..."
                  emptyMessage="لم يتم العثور على قسم."
                  onValueChange={(id) => {
                    setSelectedSection(id);
                    form.setValue("subsection_id", undefined as any, {
                      shouldValidate: true,
                    });
                    form.setValue("skill_id", null, { shouldValidate: true });
                    setSelectedSubsection(undefined);
                  }}
                />

                {/* === REPLACED WITH COMBOBOX === */}
                <SearchableCombobox
                  form={form}
                  fieldName="subsection_id"
                  label="القسم الفرعي"
                  options={subsections?.results || []}
                  placeholder="اختر قسمًا فرعيًا"
                  searchPlaceholder="ابحث عن قسم فرعي..."
                  emptyMessage="لم يتم العثور على قسم."
                  disabled={!form.watch("section_id")}
                  isLoading={isLoadingSubsections}
                  onValueChange={(id) => {
                    setSelectedSubsection(id);
                    form.setValue("skill_id", null, { shouldValidate: true });
                  }}
                />

                {/* === REPLACED WITH COMBOBOX === */}
                <SearchableCombobox
                  form={form}
                  fieldName="skill_id"
                  label="المهارة (اختياري)"
                  options={skills?.results || []}
                  placeholder="اختر مهارة"
                  searchPlaceholder="ابحث عن مهارة..."
                  emptyMessage="لم يتم العثور على مهارة."
                  disabled={!form.watch("subsection_id")}
                  isLoading={isLoadingSkills}
                  // No onValueChange needed here as it's the last in the chain
                />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                  <FormField
                    control={form.control}
                    name="difficulty"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>مستوى الصعوبة</FormLabel>
                        <Select
                          onValueChange={(v) => field.onChange(Number(v))}
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
                </div>

                <FormField
                  control={form.control}
                  name="is_active"
                  render={({ field }) => (
                    <FormItem className="flex flex-row rtl:flex-row-reverse items-center justify-between rounded-lg border p-4 shadow-sm">
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                      <div className="space-y-0.5">
                        <FormLabel>حالة السؤال</FormLabel>
                        <DialogDescription className="text-xs">
                          إذا كان غير نشط، فلن يظهر للطلاب.
                        </DialogDescription>
                      </div>
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="helpers" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>معلومات مساعدة (اختياري)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <FormField
                  control={form.control}
                  name="explanation"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>الشرح</FormLabel>
                      <DialogDescription className="text-xs pb-2">
                        شرح مفصل للإجابة الصحيحة يظهر للطالب بعد المحاولة.
                      </DialogDescription>
                      <FormControl>
                        <RichTextEditor
                          value={field.value ?? ""}
                          onChange={field.onChange}
                          placeholder="اكتب شرحاً مفصلاً للإجابة الصحيحة..."
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
                      <FormLabel>تلميح</FormLabel>
                      <DialogDescription className="text-xs pb-2">
                        تلميح يمكن للطالب طلبه أثناء حل السؤال.
                      </DialogDescription>
                      <FormControl>
                        <RichTextEditor
                          value={field.value ?? ""}
                          onChange={field.onChange}
                          placeholder="اكتب تلميحاً للطالب..."
                        />
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
                      <FormLabel>ملخص طريقة الحل</FormLabel>
                      <DialogDescription className="text-xs pb-2">
                        وصف مختصر لاستراتيجية الحل.
                      </DialogDescription>
                      <FormControl>
                        <RichTextEditor
                          value={field.value ?? ""}
                          onChange={field.onChange}
                          placeholder="اكتب ملخصاً لطريقة الحل..."
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
        {hasClassificationError && (
          <p className="text-center fill-red-500 text-red-500">
            هناك بعض البيانات ناقصة
          </p>
        )}
        <DialogFooter>
          <Button type="button" variant="outline" onClick={handleClose}>
            إلغاء
          </Button>
          <Button type="submit" disabled={isPending}>
            {isPending
              ? "جاري الحفظ..."
              : isEditMode
              ? "حفظ التغييرات"
              : "إنشاء السؤال"}
          </Button>
        </DialogFooter>
      </form>
    </Form>
  );
}

export function QuestionFormDialog({
  isOpen,
  onClose,
  questionId,
}: {
  isOpen: boolean;
  onClose: () => void;
  questionId: number | null;
}) {
  const queryClient = useQueryClient();
  const isEditMode = questionId !== null;

  const [selectedSection, setSelectedSection] = useState<number | undefined>();
  const [selectedSubsection, setSelectedSubsection] = useState<
    number | undefined
  >();
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  const [isInitialLoading, setIsInitialLoading] = useState(isEditMode);

  const { data: question, isLoading: isLoadingQuestion } = useQuery({
    queryKey: queryKeys.admin.learning.questions.detail(questionId!),
    queryFn: () => getAdminQuestionDetail(questionId!),
    enabled: isEditMode && isOpen,
  });

  const { data: sections, isLoading: isLoadingSections } = useQuery({
    queryKey: queryKeys.admin.learning.sections.list({ all: true }),
    queryFn: getAdminAllSections,
    enabled: isOpen,
  });

  const { data: subsections, isLoading: isLoadingSubsections } = useQuery({
    queryKey: queryKeys.admin.learning.subsections.list({
      sectionId: selectedSection,
    }),
    queryFn: () => getAdminAllSubSections(selectedSection!),
    enabled: isOpen && typeof selectedSection === "number",
  });

  const { data: skills, isLoading: isLoadingSkills } = useQuery({
    queryKey: queryKeys.admin.learning.skills.list({
      subsectionId: selectedSubsection,
    }),
    queryFn: () => getAdminAllSkills(selectedSubsection!),
    enabled: isOpen && typeof selectedSubsection === "number",
  });

  // --- Form Initialization ---
  const form = useForm<QuestionFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: defaultFormValues,
  });

  // --- Effect to set up dependent queries and populate form ---
  useEffect(() => {
    if (isOpen) {
      if (isEditMode && question) {
        // Step 1: Set state to trigger dependent queries
        setSelectedSection(question.section.id);
        setSelectedSubsection(question.subsection.id);
        setImagePreview(question.image);

        // Step 2: Populate the form with the question's data
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
        });
      } else if (!isEditMode) {
        // Reset everything for "Create" mode
        form.reset(defaultFormValues);
        setSelectedSection(undefined);
        setSelectedSubsection(undefined);
        setImagePreview(null);
      }
    }
  }, [isOpen, isEditMode, question, form]);

  const mutation = useMutation({
    mutationFn: (values: QuestionFormValues) => {
      if (isEditMode) {
        const payload: Partial<AdminQuestionCreateUpdate> & { image?: null } = {
          ...values,
        };

        if (payload.image_upload instanceof File) {
          const formData = objectToFormData(payload);
          return updateAdminQuestion(questionId, formData as any);
        }
        if (payload.image_upload === null) {
          payload.image = null;
          payload.image_upload = null;
        }

        return updateAdminQuestion(questionId, payload);
      } else {
        const payload: AdminQuestionCreateUpdate = values;
        return createAdminQuestion(payload);
      }
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
  // --- Handlers ---
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
  // --- THE MASTER LOADING CONDITION ---
  const isDataReadyForEdit =
    isEditMode &&
    !!question &&
    !!sections &&
    // We only need to wait for skills if the question HAS a skill
    (!!subsections || !question.skill || !!skills);

  console.log(isDataReadyForEdit);

  useEffect(() => {
    // Once the initial data is ready, we turn off the full-form skeleton forever.
    // Subsequent loading will be handled by the individual comboboxes.
    if (isDataReadyForEdit) {
      setIsInitialLoading(false);
    }
  }, [isDataReadyForEdit]);

  const showSkeleton = isEditMode && !isDataReadyForEdit && isInitialLoading;
  const showCreateForm = !isEditMode && !!sections;
  const showEditForm = isEditMode && !isInitialLoading;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="md:max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "تعديل السؤال" : "إنشاء سؤال جديد"}
          </DialogTitle>
          <DialogDescription>
            املأ التفاصيل أدناه. الحقول التي تحتوي على علامة (*) مطلوبة.
          </DialogDescription>
        </DialogHeader>

        {showSkeleton && <FormSkeleton />}

        {!showSkeleton && (showEditForm || showCreateForm) && (
          <QuestionFormComponent
            form={form}
            onSubmit={onSubmit}
            handleClose={handleClose}
            handleImageChange={handleImageChange}
            handleRemoveImage={handleRemoveImage}
            isEditMode={isEditMode}
            isPending={mutation.isPending}
            imagePreview={imagePreview}
            sections={sections!}
            subsections={subsections}
            skills={skills}
            setSelectedSection={setSelectedSection}
            setSelectedSubsection={setSelectedSubsection}
            // Pass loading states down to the form component
            isLoadingSubsections={isLoadingSubsections}
            isLoadingSkills={isLoadingSkills}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
