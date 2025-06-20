"use client";

import React, { useState, useEffect } from "react";
import { useForm, Controller, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Check, ChevronDown, ChevronUp, Loader2, Minus } from "lucide-react";

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

import { getLearningSections } from "@/services/learning.service";
import { startLevelAssessmentTest } from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import type { LearningSection } from "@/types/api/learning.types";
import type { StartLevelAssessmentPayload } from "@/types/api/study.types";
import { cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { queryKeys } from "@/constants/queryKeys";

interface StartLevelAssessmentFormValues {
  selectedSections: Record<
    string,
    {
      // Keyed by main section slug
      allSelected: boolean; // Main section checkbox state
      subsections: Record<string, boolean>; // Keyed by subsection slug
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
    num_questions: 30, // Default number of questions
  };
};

const StartLevelAssessmentForm: React.FC = () => {
  const t = useTranslations("Study.determineLevel.startForm");
  const commonT = useTranslations("Common");
  const router = useRouter();
  const queryClient = useQueryClient();
  const [mutationErrorMsg, setMutationErrorMsg] = useState<string | null>(null);

  const {
    data: learningSectionsData,
    isLoading: isLoadingSections,
    error: sectionsError,
  } = useQuery({
    queryKey: queryKeys.learning.sections({}),
    queryFn: () => getLearningSections(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  const sections = learningSectionsData?.results || [];

  const formSchema = z.object({
    selectedSections: z
      .custom<StartLevelAssessmentFormValues["selectedSections"]>()
      .refine(
        (val) => {
          // At least one main section (derived from selected subsections) must be chosen
          return Object.values(val).some((mainSection) =>
            Object.values(mainSection.subsections).some(
              (isSelected) => isSelected
            )
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
    mode: "onChange", // Validate on change for better UX
    defaultValues: createInitialFormValues(sections),
  });

  // Update defaultValues when sections are loaded
  useEffect(() => {
    if (sections.length > 0) {
      setValue(
        "selectedSections",
        createInitialFormValues(sections).selectedSections
      );
      setValue("num_questions", 30); // Reset num_questions as well
    }
  }, [sections, setValue]);

  const selectedSectionsWatched = watch("selectedSections");

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

  const handleSubSectionChange = (
    mainSectionSlug: string,
    subSectionSlug: string,
    isChecked: boolean
  ) => {
    const currentMainSection = selectedSectionsWatched[mainSectionSlug];
    const updatedSubsections = {
      ...currentMainSection.subsections,
      [subSectionSlug]: isChecked,
    };

    const allSubSelected = Object.values(updatedSubsections).every(
      (val) => val
    );
    const someSubSelected = Object.values(updatedSubsections).some(
      (val) => val
    );

    let newAllSelectedState: boolean;
    if (allSubSelected) newAllSelectedState = true;
    else if (someSubSelected) newAllSelectedState = false;
    // Treat as indeterminate, effectively false for "allSelected"
    else newAllSelectedState = false;

    setValue(
      `selectedSections.${mainSectionSlug}`,
      {
        allSelected: newAllSelectedState, // This will control the main checkbox state (true if all sub are true)
        subsections: updatedSubsections,
      },
      { shouldValidate: true }
    );
  };

  const startAssessmentMutation = useMutation({
    mutationFn: startLevelAssessmentTest,
    onSuccess: (data) => {
      setMutationErrorMsg(null);
      toast.success(t("api.startSuccess"));
      // The API response `data` includes `attempt_id` and `questions`.
      // We need to pass this to the quiz page.
      // For client components, query params or client-side state (like Zustand/Context) are options.
      // Simplest for now is query params if question data isn't too large.
      // Backend should ideally store questions against attempt_id, so quiz page just needs attempt_id.
      // Based on API doc UserTestAttemptStartResponse, it returns questions.
      // Storing in localStorage temporarily is also an option but less ideal.
      // Let's assume the quiz page will re-fetch attempt details including questions using the attempt_id.
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });
      router.push(PATHS.STUDY.DETERMINE_LEVEL.ATTEMPT(data.attempt_id));
    },
    onError: (error: any) => {
      const errorMessage = getApiErrorMessage(error, t("api.startError"));
      setMutationErrorMsg(errorMessage); // Set error for on-page Alert
      toast.error(errorMessage);
    },
  });

  const onSubmit = (formData: StartLevelAssessmentFormValues) => {
    const payloadSections: string[] = [];
    for (const mainSlug in formData.selectedSections) {
      if (
        Object.values(formData.selectedSections[mainSlug].subsections).some(
          (isSelected) => isSelected
        )
      ) {
        if (!payloadSections.includes(mainSlug)) {
          payloadSections.push(mainSlug);
        }
      }
    }

    if (payloadSections.length === 0) {
      // This should be caught by Zod validation, but as a fallback
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
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>{t("selectSectionsAndCount")}</CardTitle>
          <CardDescription>{t("selectSectionsDescription")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {errors.selectedSections && (
            <p className="text-sm font-medium text-destructive">
              {/* Ensure this message comes from Zod and is a string */}
              {typeof errors.selectedSections.message === "string"
                ? errors.selectedSections.message
                : t("validation.selectAtLeastOneSubsection")}
            </p>
          )}
          <Accordion
            type="multiple"
            defaultValue={sections.map((s) => s.slug)}
            className="w-full space-y-3"
          >
            {sections.map((section) => {
              const mainSectionState = selectedSectionsWatched?.[section.slug];
              const allSubsectionsSelected =
                mainSectionState &&
                Object.values(mainSectionState.subsections).every(Boolean);
              const someSubsectionsSelected =
                mainSectionState &&
                Object.values(mainSectionState.subsections).some(Boolean);

              const mainCheckboxState:
                | "checked"
                | "unchecked"
                | "indeterminate" = allSubsectionsSelected
                ? "checked"
                : someSubsectionsSelected
                ? "indeterminate"
                : "unchecked";

              return (
                <AccordionItem
                  value={section.slug}
                  key={section.slug}
                  className="rounded-lg border dark:border-gray-700"
                >
                  <AccordionTrigger className="p-4 hover:no-underline">
                    <div className="flex items-center space-x-3 rtl:space-x-reverse">
                      <Checkbox
                        id={`section-${section.slug}`}
                        checked={mainCheckboxState === "checked"}
                        data-state={mainCheckboxState} // For styling indeterminate
                        onCheckedChange={(checked) => {
                          handleMainSectionChange(
                            section.slug,
                            checked === true
                          );
                        }}
                        className={cn(
                          mainCheckboxState === "indeterminate" &&
                            "data-[state=indeterminate]:bg-primary data-[state=indeterminate]:border-primary data-[state=indeterminate]:text-primary-foreground"
                        )}
                        aria-label={`Select all in ${section.name}`}
                      >
                        {mainCheckboxState === "indeterminate" && (
                          <Minus className="h-4 w-4" />
                        )}
                      </Checkbox>
                      <label
                        htmlFor={`section-${section.slug}`}
                        className="cursor-pointer font-medium rtl:mr-3"
                      >
                        {section.name}
                      </label>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="grid grid-cols-1 gap-3 p-4 pt-0 sm:grid-cols-4">
                    {section.subsections.map((subsection) => (
                      <div
                        key={subsection.slug}
                        className="flex items-center space-x-3 ps-4 rtl:space-x-reverse rtl:pe-4"
                      >
                        <Checkbox
                          id={`subsection-${section.slug}-${subsection.slug}`}
                          checked={
                            selectedSectionsWatched?.[section.slug]
                              ?.subsections?.[subsection.slug] || false
                          }
                          onCheckedChange={(checked) =>
                            handleSubSectionChange(
                              section.slug,
                              subsection.slug,
                              checked === true
                            )
                          }
                        />
                        <label
                          htmlFor={`subsection-${section.slug}-${subsection.slug}`}
                          className="cursor-pointer text-sm text-muted-foreground rtl:mr-3"
                        >
                          {subsection.name}
                        </label>
                      </div>
                    ))}
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>

          <div>
            <Label htmlFor="num_questions" className="text-base font-medium">
              {t("numQuestions")}
            </Label>
            <Controller
              name="num_questions"
              control={control}
              render={({ field }) => (
                <Input
                  id="num_questions"
                  type="number"
                  {...field}
                  onChange={(e) =>
                    field.onChange(parseInt(e.target.value, 10) || 0)
                  }
                  className="mt-2"
                />
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

      <div className="flex ltr:justify-end rtl:justify-start">
        <Button
          type="submit"
          disabled={startAssessmentMutation.isPending || !isValid}
          size="lg"
          className="text-white"
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
