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
import {
  AdminQuestionCreateUpdate,
  CorrectAnswer,
} from "@/types/api/admin/learning.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Skeleton } from "@/components/ui/skeleton";

const difficultyLevels = [
  { value: 1, label: "1 - Very Easy" },
  { value: 2, label: "2 - Easy" },
  { value: 3, label: "3 - Medium" },
  { value: 4, label: "4 - Hard" },
  { value: 5, label: "5 - Very Hard" },
];

const answerOptions = ["A", "B", "C", "D"] as const;

// Zod schema is our single source of truth for validation
const formSchema = z.object({
  question_text: z
    .string()
    .min(10, "Question text must be at least 10 characters."),
  option_a: z.string().min(1, "Option A is required."),
  option_b: z.string().min(1, "Option B is required."),
  option_c: z.string().min(1, "Option C is required."),
  option_d: z.string().min(1, "Option D is required."),
  correct_answer: z.enum(answerOptions, {
    required_error: "Correct answer is required.",
  }),
  difficulty: z.coerce.number().min(1).max(5),
  section_id: z.coerce.number({ required_error: "Section is required." }),
  subsection_id: z.coerce.number({ required_error: "Subsection is required." }),
  skill_id: z.coerce.number().nullable().optional(),
  is_active: z.boolean(),
  image_upload: z.any().optional(), // field for the file itself
  explanation: z.string().optional().nullable(),
  hint: z.string().optional().nullable(),
  solution_method_summary: z.string().optional().nullable(),
});

type QuestionFormValues = z.infer<typeof formSchema>;

// Default values for creating a new question
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
      // This is crucial: update local state for cascading dropdowns after form reset.
      setSelectedSection(question.section.id);
      setSelectedSubsection(question.subsection.id);
      setImagePreview(question.image);
    } else if (!isEditMode) {
      // When opening in "create" mode, ensure it's a blank slate.
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
      toast.success(
        `Question ${isEditMode ? "updated" : "created"} successfully!`
      );
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
      toast.error(getApiErrorMessage(error, "Failed to save question."));
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
            {isEditMode ? "Edit Question" : "Create New Question"}
          </DialogTitle>
          <DialogDescription>
            Fill in the details below. All fields with an asterisk (*) are
            required.
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-6">
                  {/* Hierarchy Selects */}
                  <FormField
                    control={form.control}
                    name="section_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Section *</FormLabel>
                        <Select
                          onValueChange={(v) => {
                            field.onChange(v);
                            setSelectedSection(Number(v));
                            form.setValue("subsection_id", undefined as any);
                            form.setValue("skill_id", undefined);
                            setSelectedSubsection(undefined);
                          }}
                          value={field.value?.toString()}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select a section" />
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
                        <FormLabel>Subsection *</FormLabel>
                        <Select
                          onValueChange={(v) => {
                            field.onChange(v);
                            setSelectedSubsection(Number(v));
                            form.setValue("skill_id", undefined);
                          }}
                          value={field.value?.toString()}
                          disabled={!selectedSection}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select a subsection" />
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
                        <FormLabel>Skill (Optional)</FormLabel>
                        <Select
                          onValueChange={field.onChange}
                          value={field.value?.toString()}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select a skill" />
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
                        <FormLabel>Image (Optional)</FormLabel>
                        {imagePreview && (
                          <div className="mt-2">
                            <img
                              src={imagePreview}
                              alt="Preview"
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
                            Remove Image
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
                        <FormLabel>Question Text *</FormLabel>
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
                        <FormLabel>Option A *</FormLabel>
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
                        <FormLabel>Option B *</FormLabel>
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
                        <FormLabel>Option C *</FormLabel>
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
                        <FormLabel>Option D *</FormLabel>
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
                      <FormLabel>Correct Answer *</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select correct option" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {answerOptions.map((opt) => (
                            <SelectItem key={opt} value={opt}>
                              Option {opt}
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
                      <FormLabel>Difficulty *</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value?.toString()}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select difficulty" />
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
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 shadow-sm mt-8">
                      <FormLabel>Active</FormLabel>
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
                      <FormLabel>Explanation (Optional)</FormLabel>
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
                      <FormLabel>Hint (Optional)</FormLabel>
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
                      <FormLabel>Solution Summary (Optional)</FormLabel>
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
                  Cancel
                </Button>
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending
                    ? "Saving..."
                    : isEditMode
                    ? "Save Changes"
                    : "Create Question"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        )}
      </DialogContent>
    </Dialog>
  );
}
