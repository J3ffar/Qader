"use client";

import React, { useState, useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Check, Loader2, Minus, Sparkles, Target } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Switch } from "@/components/ui/switch";

import { getLearningSections } from "@/services/learning.service";
import { startPracticeSimulationTest } from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import type { LearningSection } from "@/types/api/learning.types";
import type { StartPracticeSimulationPayload } from "@/types/api/study.types";
import { cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

// Form Schema Definition
const createFormSchema = (t: any) =>
  z.object({
    test_type: z.enum(["practice", "simulation"]),
    subsections: z
      .array(z.string())
      .min(1, t("validation.atLeastOneSubsection")),
    num_questions: z.coerce
      .number()
      .min(5, t("validation.numQuestionsMin"))
      .max(120, t("validation.numQuestionsMax")),
    starred: z.boolean(),
    not_mastered: z.boolean(),
  });

// Component
const StartTestForm: React.FC = () => {
  const t = useTranslations("Study.tests.startForm");
  const commonT = useTranslations("Common");
  const router = useRouter();
  const [mutationErrorMsg, setMutationErrorMsg] = useState<string | null>(null);

  const formSchema = createFormSchema(t);
  type FormValues = z.infer<typeof formSchema>;

  const { data: learningSectionsData, isLoading: isLoadingSections } = useQuery(
    {
      queryKey: [QUERY_KEYS.LEARNING_SECTIONS],
      queryFn: () => getLearningSections(),
      staleTime: 10 * 60 * 1000,
    }
  );
  const sections = learningSectionsData?.results || [];

  const { control, handleSubmit, setValue, watch } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    mode: "onChange",
    defaultValues: {
      test_type: "practice",
      subsections: [],
      num_questions: 25,
      starred: false,
      not_mastered: false,
    },
  });

  const watchedSubsections = watch("subsections");
  const watchedTestType = watch("test_type");

  useEffect(() => {
    if (watchedTestType === "simulation") {
      setValue("num_questions", 120); // Example: A full simulation has 120 questions
    }
  }, [watchedTestType, setValue]);

  const startTestMutation = useMutation({
    mutationFn: startPracticeSimulationTest,
    onSuccess: (data) => {
      toast.success(t("api.startSuccess"));
      router.push(PATHS.STUDY.TESTS.ATTEMPT(data.attempt_id));
    },
    onError: (error: any) => {
      const errorMessage = getApiErrorMessage(error, commonT("errors.generic"));
      setMutationErrorMsg(errorMessage);
    },
  });

  const onSubmit = (formData: FormValues) => {
    const payload: StartPracticeSimulationPayload = {
      test_type: formData.test_type,
      config: {
        subsections: formData.subsections,
        num_questions: formData.num_questions,
        starred: formData.starred,
        not_mastered: formData.not_mastered,
      },
    };
    startTestMutation.mutate(payload);
  };

  if (isLoadingSections) return <StartTestFormSkeleton />;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      {mutationErrorMsg && (
        <Alert variant="destructive">
          <AlertTitle>{commonT("errors.requestFailed")}</AlertTitle>
          <AlertDescription>{mutationErrorMsg}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t("settingsTitle")}</CardTitle>
          <CardDescription>{t("settingsDescription")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label className="text-base font-medium">{t("testType")}</Label>
            <Controller
              name="test_type"
              control={control}
              render={({ field }) => (
                <ToggleGroup
                  type="single"
                  defaultValue={field.value}
                  onValueChange={field.onChange}
                  className="mt-2 grid grid-cols-2"
                >
                  <ToggleGroupItem value="practice" aria-label="Practice Test">
                    <Sparkles className="me-2 h-4 w-4" /> {t("practice")}
                  </ToggleGroupItem>
                  <ToggleGroupItem
                    value="simulation"
                    aria-label="Simulation Test"
                  >
                    <Target className="me-2 h-4 w-4" /> {t("simulation")}
                  </ToggleGroupItem>
                </ToggleGroup>
              )}
            />
          </div>

          <Accordion
            type="multiple"
            defaultValue={sections.map((s) => s.slug)}
            className="w-full space-y-3"
          >
            {sections.map((section) => (
              <AccordionItem
                value={section.slug}
                key={section.slug}
                className="rounded-lg border dark:border-gray-700"
              >
                <AccordionTrigger className="p-4 font-medium hover:no-underline">
                  {section.name}
                </AccordionTrigger>
                <AccordionContent className="grid grid-cols-1 gap-3 p-4 pt-0 sm:grid-cols-2">
                  {section.subsections.map((subsection) => (
                    <div
                      key={subsection.slug}
                      className="flex items-center space-x-2 rtl:space-x-reverse"
                    >
                      <Checkbox
                        id={subsection.slug}
                        checked={watchedSubsections.includes(subsection.slug)}
                        onCheckedChange={(checked) => {
                          const newSubsections = checked
                            ? [...watchedSubsections, subsection.slug]
                            : watchedSubsections.filter(
                                (s) => s !== subsection.slug
                              );
                          setValue("subsections", newSubsections, {
                            shouldValidate: true,
                          });
                        }}
                      />
                      <label
                        htmlFor={subsection.slug}
                        className="cursor-pointer text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                      >
                        {subsection.name}
                      </label>
                    </div>
                  ))}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>

          <div>
            <Label htmlFor="num_questions" className="text-base font-medium">
              {t("numQuestions")}
            </Label>
            <Controller
              name="num_questions"
              control={control}
              render={({ field, fieldState }) => (
                <>
                  <Input
                    id="num_questions"
                    type="number"
                    {...field}
                    disabled={watchedTestType === "simulation"}
                    className="mt-2"
                  />
                  {fieldState.error && (
                    <p className="mt-1 text-sm text-destructive">
                      {fieldState.error.message}
                    </p>
                  )}
                </>
              )}
            />
          </div>

          <div className="space-y-4">
            <Controller
              name="starred"
              control={control}
              render={({ field }) => (
                <div className="flex items-center space-x-2 rounded-md border p-3 rtl:space-x-reverse">
                  <Switch
                    id="starred-switch"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                  <Label
                    htmlFor="starred-switch"
                    className="flex-1 cursor-pointer"
                  >
                    {t("starredLabel")}
                  </Label>
                </div>
              )}
            />
            <Controller
              name="not_mastered"
              control={control}
              render={({ field }) => (
                <div className="flex items-center space-x-2 rounded-md border p-3 rtl:space-x-reverse">
                  <Switch
                    id="not-mastered-switch"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                  <Label
                    htmlFor="not-mastered-switch"
                    className="flex-1 cursor-pointer"
                  >
                    {t("notMasteredLabel")}
                  </Label>
                </div>
              )}
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button type="submit" disabled={startTestMutation.isPending} size="lg">
          {startTestMutation.isPending && (
            <Loader2 className="me-2 h-5 w-5 animate-spin" />
          )}
          {startTestMutation.isPending ? commonT("loading") : t("submit")}
        </Button>
      </div>
    </form>
  );
};

const StartTestFormSkeleton: React.FC = () => (
  // ... Skeleton implementation here ...
  <div>Loading form...</div>
);

export default StartTestForm;
