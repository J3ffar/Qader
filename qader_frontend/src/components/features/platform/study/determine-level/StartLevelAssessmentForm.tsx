// qader_frontend/src/components/features/platform/study/determine-level/StartLevelAssessmentForm.tsx
"use client";

import React, { useState, useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Info, Loader2, Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
// REMOVED: Checkbox is no longer needed.
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";

import { getLearningSections } from "@/services/learning.service";
import { startLevelAssessmentTest } from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import type { LearningSection } from "@/types/api/learning.types";
import type { StartLevelAssessmentPayload } from "@/types/api/study.types";
import { cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { queryKeys } from "@/constants/queryKeys";
import { useAuthCore } from "@/store/auth.store";

// SIMPLIFIED: State is now a simple map of section slugs to a boolean.
interface StartLevelAssessmentFormValues {
  selectedSections: Record<string, boolean>;
  num_questions: number;
}

// SIMPLIFIED: Creates a simple map where each section is initially not selected.
const createInitialFormValues = (
  sections: LearningSection[]
): StartLevelAssessmentFormValues => {
  const initialSelectedSections: StartLevelAssessmentFormValues["selectedSections"] =
    {};
  sections.forEach((section) => {
    initialSelectedSections[section.slug] = false;
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

  // SIMPLIFIED: Schema validation works on the new, simpler data structure.
  const formSchema = z.object({
    selectedSections: z.record(z.boolean()).refine(
      (val) => {
        return Object.values(val).some((isSelected) => isSelected);
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

  // SIMPLIFIED: A single handler to toggle the selection state of a card.
  const handleSectionSelect = (sectionSlug: string) => {
    const currentValue = selectedSectionsWatched?.[sectionSlug] || false;
    setValue(`selectedSections.${sectionSlug}`, !currentValue, {
      shouldValidate: true,
    });
  };

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

  // SIMPLIFIED: Submission logic is much clearer with the new state shape.
  const onSubmit = (formData: StartLevelAssessmentFormValues) => {
    const payloadSections: string[] = Object.entries(formData.selectedSections)
      .filter(([_, isSelected]) => isSelected)
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

          <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-6">
            {sections.map((section) => {
              const isSectionSelected =
                selectedSectionsWatched?.[section.slug] || false;

              return (
                <div
                  key={section.slug}
                  onClick={() => handleSectionSelect(section.slug)}
                  className={cn(
                    "w-full max-w-full rounded-2xl border-2 p-6 shadow-md transition-all duration-200 cursor-pointer",
                    isSectionSelected
                      ? "border-primary bg-primary/5 dark:bg-[#074182]/50"
                      : "border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500"
                  )}
                  role="checkbox"
                  aria-checked={isSectionSelected}
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === " " || e.key === "Enter") {
                      e.preventDefault();
                      handleSectionSelect(section.slug);
                    }
                  }}
                >
                  <div className="flex items-start justify-between gap-4">
                    <h3 className="font-semibold text-lg sm:text-xl pr-8">
                      {section.name}
                    </h3>
                    <div
                      className={cn(
                        "flex-shrink-0 h-6 w-6 rounded-full border-2 flex items-center justify-center transition-all",
                        isSectionSelected
                          ? "bg-primary border-primary text-primary-foreground"
                          : "bg-transparent border-muted-foreground"
                      )}
                      aria-hidden="true"
                    >
                      {isSectionSelected && <Check className="h-4 w-4" />}
                    </div>
                  </div>

                  <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {section.subsections.map((subsection) => (
                      <div
                        key={subsection.slug}
                        className={cn(
                          "rounded-lg p-3 text-center text-sm select-none border",
                          isSectionSelected
                            ? "border-primary/50 bg-primary/10 font-medium"
                            : "border-gray-300 dark:border-gray-600 bg-muted/50 text-muted-foreground"
                        )}
                      >
                        {subsection.name}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="w-full pt-4 border-t dark:border-gray-700">
            <Label
              htmlFor="num_questions"
              className="text-base font-medium flex justify-center"
            >
              {t("numQuestions")}
            </Label>
            <Controller
              name="num_questions"
              control={control}
              render={({ field }) => (
                <div className="mt-2 flex justify-center items-center gap-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() =>
                      field.onChange(Math.max((field.value || 0) - 1, 5))
                    }
                    className="w-10 h-10 p-0 text-xl cursor-pointer"
                  >
                    –
                  </Button>
                  <input
                    type="text"
                    id="num_questions"
                    value={field.value || ""}
                    onChange={(e) => {
                      const value = parseInt(e.target.value, 10);
                      field.onChange(isNaN(value) ? "" : value);
                    }}
                    onBlur={() => {
                      // Validate on blur to clamp value between 5 and 100
                      const value = Math.max(
                        5,
                        Math.min(100, field.value || 30)
                      );
                      field.onChange(value);
                    }}
                    className="w-16 text-center text-lg font-semibold border rounded-md px-2 py-1 dark:bg-transparent dark:border-gray-600"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() =>
                      field.onChange(Math.min((field.value || 0) + 1, 100))
                    }
                    className="w-10 h-10 p-0 text-xl cursor-pointer"
                  >
                    +
                  </Button>
                </div>
              )}
            />
            {errors.num_questions && (
              <p className="mt-2 text-sm text-center font-medium text-destructive">
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
  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <Skeleton className="mb-2 h-7 w-3/5" />
          <Skeleton className="h-4 w-4/5" />
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="rounded-2xl border p-6 space-y-4 dark:border-gray-700"
              >
                <div className="flex items-start justify-between">
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-6 w-6 rounded-full" />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              </div>
            ))}
          </div>
          <div className="pt-4 border-t dark:border-gray-700">
            <Skeleton className="h-6 w-1/4 mx-auto mb-2" />
            <div className="flex justify-center items-center gap-4">
              <Skeleton className="h-10 w-10" />
              <Skeleton className="h-10 w-16" />
              <Skeleton className="h-10 w-10" />
            </div>
          </div>
        </CardContent>
      </Card>
      <div className="flex justify-center">
        <Skeleton className="h-12 w-full max-w-xs" />
      </div>
    </div>
  );
};

export default StartLevelAssessmentForm;
