"use client";

import React, { useState, useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Info, Loader2, Check } from "lucide-react"; // REMOVED: Minus icon

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
} from "@/components/ui/accordion";

import { getLearningSections } from "@/services/learning.service";
import { startLevelAssessmentTest } from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import type { LearningSection } from "@/types/api/learning.types";
import type { StartLevelAssessmentPayload } from "@/types/api/study.types";
import { cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { queryKeys } from "@/constants/queryKeys";
import { useAuthCore } from "@/store/auth.store";

interface StartLevelAssessmentFormValues {
  selectedSections: Record<
    string,
    {
      allSelected: boolean;
      subsections: Record<string, boolean>;
    }
  >;
  num_questions: number;
}

const createInitialFormValues = (
  sections: LearningSection[]
): StartLevelAssessmentFormValues => {
  const initialSelectedSections: StartLevelAssessmentFormValues["selectedSections"] =
    {};
  sections.forEach((section) => {
    initialSelectedSections[section.slug] = {
      allSelected: false,
      subsections: section.subsections.reduce((acc, sub) => {
        acc[sub.slug] = false;
        return acc;
      }, {} as Record<string, boolean>),
    };
  });
  return {
    selectedSections: initialSelectedSections,
    num_questions: 30,
  };
};

const StartLevelAssessmentForm: React.FC = () => {
  const t = useTranslations("Study.determineLevel.startForm");
  const commonT = useTranslations("Common");
  const router = useRouter();
  const queryClient = useQueryClient();
  const [mutationErrorMsg, setMutationErrorMsg] = useState<string | null>(null);

  const { user } = useAuthCore();
  const isFirstTimeAssessment = user?.level_determined === false;

  const { data: learningSectionsData, isLoading: isLoadingSections } = useQuery(
    {
      queryKey: queryKeys.learning.sections({}),
      queryFn: () => getLearningSections(),
      staleTime: 5 * 60 * 1000,
    }
  );

  const sections = learningSectionsData?.results || [];

  const formSchema = z.object({
    selectedSections: z
      .custom<StartLevelAssessmentFormValues["selectedSections"]>()
      .refine(
        (val) => {
          return Object.values(val).some(
            (mainSection) => mainSection.allSelected
          );
        },
        { message: t("validation.atLeastOneSection") }
      ),
    num_questions: z
      .number()
      .min(5, t("validation.numQuestionsMin"))
      .max(100, t("validation.numQuestionsMax")),
  });

  const {
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isValid },
  } = useForm<StartLevelAssessmentFormValues>({
    resolver: zodResolver(formSchema),
    mode: "onChange",
    defaultValues: createInitialFormValues(sections),
  });

  useEffect(() => {
    if (sections.length > 0) {
      setValue(
        "selectedSections",
        createInitialFormValues(sections).selectedSections
      );
      setValue("num_questions", 30);
    }
  }, [sections, setValue]);

  const selectedSectionsWatched = watch("selectedSections");

  // SIMPLIFIED: This is now the only function needed to change selections.
  const handleMainSectionChange = (sectionSlug: string, isChecked: boolean) => {
    const currentMainSection = selectedSectionsWatched[sectionSlug];
    const updatedSubsections: Record<string, boolean> = {};
    for (const subSlug in currentMainSection.subsections) {
      updatedSubsections[subSlug] = isChecked;
    }
    setValue(
      `selectedSections.${sectionSlug}`,
      { allSelected: isChecked, subsections: updatedSubsections },
      { shouldValidate: true }
    );
  };

  // REMOVED: handleSubSectionChange is no longer needed.

  const startAssessmentMutation = useMutation({
    mutationFn: startLevelAssessmentTest,
    onSuccess: (data) => {
      setMutationErrorMsg(null);
      toast.success(t("api.startSuccess"));
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });
      router.push(PATHS.STUDY.DETERMINE_LEVEL.ATTEMPT(data.attempt_id));
    },
    onError: (error: any) => {
      const errorMessage = getApiErrorMessage(error, t("api.startError"));
      setMutationErrorMsg(errorMessage);
      toast.error(errorMessage);
    },
  });

  const onSubmit = (formData: StartLevelAssessmentFormValues) => {
    // SIMPLIFIED: Submission logic is clearer now.
    const payloadSections: string[] = Object.entries(formData.selectedSections)
      .filter(([_, sectionData]) => sectionData.allSelected)
      .map(([mainSlug, _]) => mainSlug);

    if (payloadSections.length === 0) {
      toast.error(t("validation.atLeastOneSection"));
      return;
    }

    const payload: StartLevelAssessmentPayload = {
      sections: payloadSections,
      num_questions: formData.num_questions,
    };
    startAssessmentMutation.mutate(payload);
  };

  if (isLoadingSections) {
    return <StartLevelAssessmentFormSkeleton />;
  }
  {
    mutationErrorMsg && (
      <Alert variant="destructive" className="mb-4">
        <AlertTitle>
          {t("api.startError") /* Add this translation */}
        </AlertTitle>
        <AlertDescription>{mutationErrorMsg}</AlertDescription>
      </Alert>
    );
  }

  if (sections.length === 0 && !isLoadingSections) {
    return (
      <Alert variant="default">
        <AlertTitle>{t("errors.noSectionsAvailableTitle")}</AlertTitle>
        <AlertDescription>
          {t("errors.noSectionsAvailableDescription")}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8 w-full">
      {isFirstTimeAssessment && (
        <Alert className="dark:bg-[#074182]/20 dark:border-[#7E89AC]">
          <Info className="h-4 w-4" />
          <AlertTitle>{t("firstTime.title")}</AlertTitle>
          <AlertDescription>{t("firstTime.description")}</AlertDescription>
        </Alert>
      )}

      {mutationErrorMsg && (
        <Alert variant="destructive" className="mb-4">
          <AlertTitle>{t("api.startError")}</AlertTitle>
          <AlertDescription>{mutationErrorMsg}</AlertDescription>
        </Alert>
      )}

      <Card className="overflow-hidden w-full max-w-none dark:bg-[#0B1739] dark:border-[#7E89AC]">
        <CardHeader>
          <CardTitle>{t("selectSectionsAndCount")}</CardTitle>
          {/* UPDATED: New description reflects simplified interaction */}
          <CardDescription>{t("selectSectionsDescriptionNew")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {errors.selectedSections && (
            <p className="text-sm font-medium text-destructive">
              {typeof errors.selectedSections.message === "string"
                ? errors.selectedSections.message
                : t("validation.selectAtLeastOneSubsection")}
            </p>
          )}
          <Accordion
            type="multiple"
            defaultValue={sections.map((s) => s.slug)}
            className="w-full grid grid-cols-1 md:grid-cols-2 gap-6"
          >
            {sections.map((section) => {
              // SIMPLIFIED: Main checkbox is either checked or not. No indeterminate state.
              const isSectionSelected =
                selectedSectionsWatched?.[section.slug]?.allSelected || false;

              return (
                <AccordionItem
                  value={section.slug}
                  key={section.slug}
                  className="w-full max-w-full rounded-2xl border-2 p-6 shadow-md dark:border-gray-700"
                >
                  <div className="flex items-center space-x-3 rtl:space-x-reverse mb-4">
                    <Checkbox
                      id={`section-${section.slug}`}
                      checked={isSectionSelected}
                      onCheckedChange={(checked) =>
                        handleMainSectionChange(section.slug, checked === true)
                      }
                      className="cursor-pointer"
                      aria-label={`Select all in ${section.name}`}
                    />
                    <label
                      htmlFor={`section-${section.slug}`}
                      className="cursor-pointer font-semibold text-lg sm:text-xl rtl:mr-3"
                    >
                      {section.name}
                    </label>
                  </div>

                  <AccordionContent className="grid grid-cols-1 gap-3 p-4 pt-0 sm:grid-cols-3">
                    {section.subsections.map((subsection) => (
                      // CHANGED: Subsections are now purely informational.
                      // No onClick, no complex styling.
                      <div
                        key={subsection.slug}
                        className={cn(
                          "rounded-lg p-4 text-center text-sm select-none border",
                          isSectionSelected
                            ? "border-primary/50 bg-primary/10 dark:bg-[#074182]/50 font-medium"
                            : "border-gray-300 dark:border-gray-600 bg-muted/50 text-muted-foreground"
                        )}
                      >
                        {subsection.name}
                      </div>
                    ))}
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>

          <div className="w-full">
            <Label
              htmlFor="num_questions"
              className="text-base font-medium justify-center"
            >
              {t("numQuestions")}
            </Label>
            <Controller // make a custom number input with increment/decrement buttons
              name="num_questions"
              control={control}
              render={({ field }) => (
                <div className="mt-2 flex justify-center items-center gap-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() =>
                      field.onChange(Math.max((field.value || 0) - 1, 0))
                    }
                    className="w-10 h-10 p-0 text-xl cursor-pointer"
                  >
                    –
                  </Button>

                  <input
                    type="text"
                    value={field.value || ""}
                    onChange={(e) => {
                      const value = parseInt(e.target.value, 10);
                      field.onChange(isNaN(value) ? "" : Math.max(value, 0)); // prevent negative
                    }}
                    className="w-16 text-center text-lg font-semibold border rounded px-2 py-1"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => field.onChange((field.value || 0) + 1)}
                    className="w-10 h-10 p-0 text-xl cursor-pointer"
                  >
                    +
                  </Button>
                </div>
              )}
            />

            {errors.num_questions && (
              <p className="mt-1 text-sm font-medium text-destructive">
                {errors.num_questions.message}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-center">
        <Button
          type="submit"
          disabled={startAssessmentMutation.isPending || !isValid}
          size="lg"
          className="text-white w-full max-w-xs cursor-pointer"
        >
          {startAssessmentMutation.isPending && (
            <Loader2 className="me-2 h-5 w-5 animate-spin rtl:me-0 rtl:ms-2" />
          )}
          {startAssessmentMutation.isPending ? commonT("loading") : t("submit")}
        </Button>
      </div>
    </form>
  );
};

const StartLevelAssessmentFormSkeleton: React.FC = () => {
  const t = useTranslations("Study.determineLevel.startForm");
  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <Skeleton className="mb-2 h-7 w-3/5" />
          <Skeleton className="h-4 w-4/5" />
        </CardHeader>
        <CardContent className="space-y-6">
          <Skeleton className="mb-4 h-4 w-1/3" />{" "}
          {/* Error message placeholder */}
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="rounded-lg border p-4 dark:border-gray-700"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3 rtl:space-x-reverse">
                    <Skeleton className="h-6 w-6 rounded" />
                    <Skeleton className="h-5 w-32" />
                  </div>
                  <Skeleton className="h-6 w-6" /> {/* Chevron */}
                </div>
              </div>
            ))}
          </div>
          <div>
            <Skeleton className="mb-2 h-6 w-1/4" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="mt-1 h-4 w-1/2" />
          </div>
        </CardContent>
      </Card>
      <div className="flex justify-end">
        <Skeleton className="h-12 w-32" />
      </div>
    </div>
  );
};

export default StartLevelAssessmentForm;
