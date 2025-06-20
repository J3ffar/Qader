"use client";

import React, { ReactNode } from "react";
import { useForm, Controller, FieldError } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Loader2, Minus, Sparkles } from "lucide-react";

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
import { Switch } from "@/components/ui/switch";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getLearningSections } from "@/services/learning.service";
import { startTraditionalPractice } from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import type {
  LearningSection,
  PaginatedLearningSections,
} from "@/types/api/learning.types";
import { queryKeys } from "@/constants/queryKeys";

interface FormValues {
  selectedSubsections: Record<string, boolean>;
  num_questions: number;
  starred: boolean;
  not_mastered: boolean;
}

const TraditionalLearningConfigForm: React.FC = () => {
  const t = useTranslations("Study.traditionalLearning.config");
  const commonT = useTranslations("Common");
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: learningSectionsData, error: sectionsError } = useQuery({
    queryKey: queryKeys.learning.sections({}),
    queryFn: () => getLearningSections(),
    staleTime: 5 * 60 * 1000,
  });
  const sections: LearningSection[] =
    (learningSectionsData as PaginatedLearningSections)?.results || [];

  const formSchema = z.object({
    selectedSubsections: z
      .record(z.boolean())
      .refine((val) => Object.values(val).some(Boolean), {
        message: t("validation.atLeastOneSubsection"),
      }),
    num_questions: z.coerce
      .number()
      .int()
      .min(1, t("validation.numQuestionsMin"))
      .max(50, t("validation.numQuestionsMax")),
    starred: z.boolean(),
    not_mastered: z.boolean(),
  });

  const {
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isValid },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    mode: "onChange",
    defaultValues: {
      selectedSubsections: {},
      num_questions: 20,
      starred: false,
      not_mastered: false,
    },
  });

  const selectedSubsectionsWatched = watch("selectedSubsections");

  const handleMainSectionChange = (
    section: LearningSection,
    isChecked: boolean
  ) => {
    section.subsections.forEach((sub) => {
      setValue(`selectedSubsections.${sub.slug}`, isChecked, {
        shouldValidate: true,
      });
    });
  };

  const startPracticeMutation = useMutation({
    mutationFn: startTraditionalPractice,
    onSuccess: (data) => {
      toast.success(t("api.startSuccess"));
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });

      router.push(PATHS.STUDY.TRADITIONAL_LEARNING.SESSION(data.attempt_id));
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, t("api.startError")));
    },
  });

  const onSubmit = (formData: FormValues) => {
    const payload = {
      subsections: Object.entries(formData.selectedSubsections)
        .filter(([, isSelected]) => isSelected)
        .map(([slug]) => slug),
      num_questions: formData.num_questions,
      starred: formData.starred,
      not_mastered: formData.not_mastered,
    };
    startPracticeMutation.mutate(payload);
  };

  if (sectionsError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>{commonT("errors.fetchFailedTitle")}</AlertTitle>
        <AlertDescription>
          {getApiErrorMessage(sectionsError, t("api.startError"))}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="mx-auto max-w-4xl space-y-8"
    >
      <Card>
        <CardHeader>
          <CardTitle>{t("sectionsTitle")}</CardTitle>
          <CardDescription>{t("sectionsDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          {errors.selectedSubsections && (
            <p className="mb-4 text-sm font-medium text-destructive">
              {errors.selectedSubsections.message as ReactNode}
            </p>
          )}
          <Accordion
            type="multiple"
            defaultValue={sections.map((s) => s.slug)}
            className="w-full space-y-3"
          >
            {sections.map((section) => {
              const allSubSelected = section.subsections.every(
                (sub) => selectedSubsectionsWatched[sub.slug]
              );
              const someSubSelected = section.subsections.some(
                (sub) => selectedSubsectionsWatched[sub.slug]
              );
              const mainCheckboxState = allSubSelected
                ? "checked"
                : someSubSelected
                ? "indeterminate"
                : "unchecked";

              return (
                <AccordionItem
                  value={section.slug}
                  key={section.slug}
                  className="rounded-lg border"
                >
                  <AccordionTrigger className="p-4 hover:no-underline">
                    <div className="flex items-center space-x-3 rtl:space-x-reverse">
                      <Checkbox
                        id={`section-${section.slug}`}
                        checked={mainCheckboxState === "checked"}
                        data-state={mainCheckboxState}
                        onCheckedChange={(checked) =>
                          handleMainSectionChange(section, checked === true)
                        }
                        className={
                          mainCheckboxState === "indeterminate"
                            ? "data-[state=indeterminate]:bg-primary data-[state=indeterminate]:border-primary data-[state=indeterminate]:text-primary-foreground"
                            : ""
                        }
                        aria-label={`Select all in ${section.name}`}
                      >
                        {mainCheckboxState === "indeterminate" && (
                          <Minus className="h-4 w-4" />
                        )}
                      </Checkbox>
                      <label
                        htmlFor={`section-${section.slug}`}
                        className="cursor-pointer font-medium"
                      >
                        {section.name}
                      </label>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="grid grid-cols-2 gap-x-8 gap-y-3 p-4 pt-0">
                    {section.subsections.map((sub) => (
                      <div
                        key={sub.slug}
                        className="flex items-center space-x-3 ps-4 rtl:space-x-reverse"
                      >
                        <Controller
                          name={`selectedSubsections.${sub.slug}`}
                          control={control}
                          defaultValue={false}
                          render={({ field }) => (
                            <Checkbox
                              id={sub.slug}
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          )}
                        />
                        <Label
                          htmlFor={sub.slug}
                          className="cursor-pointer text-sm text-muted-foreground"
                        >
                          {sub.name}
                        </Label>
                      </div>
                    ))}
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("advancedOptionsTitle")}</CardTitle>
          <CardDescription>{t("advancedOptionsDescription")}</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-8 md:grid-cols-2">
          <div>
            <Label htmlFor="num_questions" className="font-medium">
              {t("numQuestionsLabel")}
            </Label>
            <Controller
              name="num_questions"
              control={control}
              render={({ field }) => (
                <Input
                  id="num_questions"
                  type="number"
                  {...field}
                  className="mt-2"
                  placeholder={t("numQuestionsPlaceholder")}
                />
              )}
            />
            {errors.num_questions && (
              <p className="mt-1 text-sm font-medium text-destructive">
                {errors.num_questions.message}
              </p>
            )}
          </div>
          <div className="space-y-6">
            <Controller
              name="starred"
              control={control}
              render={({ field }) => (
                <div className="flex items-center justify-between space-x-4 rounded-lg border p-4 rtl:space-x-reverse">
                  <div className="space-y-0.5">
                    <Label htmlFor="starred" className="text-base">
                      {t("starredLabel")}
                    </Label>
                    <p className="text-[0.8rem] text-muted-foreground">
                      {t("starredDescription")}
                    </p>
                  </div>
                  <Switch
                    id="starred"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </div>
              )}
            />
            <Controller
              name="not_mastered"
              control={control}
              render={({ field }) => (
                <div className="flex items-center justify-between space-x-4 rounded-lg border p-4 rtl:space-x-reverse">
                  <div className="space-y-0.5">
                    <Label htmlFor="not_mastered" className="text-base">
                      {t("notMasteredLabel")}
                    </Label>
                    <p className="text-[0.8rem] text-muted-foreground">
                      {t("notMasteredDescription")}
                    </p>
                  </div>
                  <Switch
                    id="not_mastered"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </div>
              )}
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button
          type="submit"
          disabled={startPracticeMutation.isPending || !isValid}
          size="lg"
        >
          {startPracticeMutation.isPending && (
            <Loader2 className="me-2 h-5 w-5 animate-spin" />
          )}
          <Sparkles className="me-2 h-5 w-5" />
          {startPracticeMutation.isPending
            ? commonT("loading")
            : t("startSession")}
        </Button>
      </div>
    </form>
  );
};

export default TraditionalLearningConfigForm;
