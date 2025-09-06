"use client";

import React, { useState, useEffect, useRef } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Check, Loader2, Minus, Sparkles, Target } from "lucide-react";
import { gsap } from "gsap";

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
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Switch } from "@/components/ui/switch";

import { getLearningSections } from "@/services/learning.service";
import { startPracticeSimulationTest } from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import type { LearningSection } from "@/types/api/learning.types";
import type { StartPracticeSimulationPayload } from "@/types/api/study.types";
import { cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { queryKeys } from "@/constants/queryKeys";

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
      .max(150, t("validation.numQuestionsMax")),
    num_sections: z.coerce
      .number()
      .min(1, t("validation.numSectionsMin", { min: 1 }))
      .max(10, t("validation.numSectionsMax", { max: 10 })),
    starred: z.boolean(),
    not_mastered: z.boolean(),
  });

// Component
const StartTestForm: React.FC = () => {
  const t = useTranslations("Study.tests.startForm");
  const commonT = useTranslations("Common");
  const router = useRouter();
  const queryClient = useQueryClient();

  // Refs for GSAP animations
  const formRef = useRef<HTMLFormElement>(null);
  const settingsCardRef = useRef<HTMLDivElement>(null);
  const sectionsCardRef = useRef<HTMLDivElement>(null);
  const optionsCardRef = useRef<HTMLDivElement>(null);
  const submitButtonRef = useRef<HTMLDivElement>(null);
  const sectionCardsRef = useRef<(HTMLDivElement | null)[]>([]);

  const formSchema = createFormSchema(t);
  type FormValues = z.infer<typeof formSchema>;

  const {
    data: learningSectionsData,
    isLoading: isLoadingSections,
    error: sectionsError,
  } = useQuery({
    queryKey: queryKeys.learning.sections({}),
    queryFn: () => getLearningSections(),
    staleTime: 10 * 60 * 1000,
  });
  const sections = learningSectionsData?.results || [];

  const { control, handleSubmit, setValue, watch, formState: { errors, isValid } } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    mode: "onChange",
    defaultValues: {
      test_type: "practice",
      subsections: [],
      num_questions: 25,
      num_sections: 3,
      starred: false,
      not_mastered: false,
    },
  });

  // sectionsTitle
  const watchedSubsections = watch("subsections");
  const watchedTestType = watch("test_type");

  // GSAP Animation Effect
  useEffect(() => {
    if (!formRef.current || isLoadingSections) return;

    const ctx = gsap.context(() => {
      const mainTl = gsap.timeline({
        defaults: {
          ease: "power3.out",
        }
      });

      // Set initial states
      gsap.set([
        settingsCardRef.current,
        sectionsCardRef.current,
        optionsCardRef.current,
        submitButtonRef.current
      ], {
        opacity: 0,
        y: 40,
        scale: 0.95
      });

      // Animate main cards in sequence
      mainTl
        .to(settingsCardRef.current, {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.6,
        })
        .to(sectionsCardRef.current, {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.6,
        }, "-=0.4")
        .to(optionsCardRef.current, {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.6,
        }, "-=0.4")
        .to(submitButtonRef.current, {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.5,
        }, "-=0.3");

      // Animate section cards with stagger
      const validSectionCards = sectionCardsRef.current.filter(item => item !== null);
      if (validSectionCards.length > 0) {
        gsap.fromTo(
          validSectionCards,
          {
            opacity: 0,
            y: 30,
            scale: 0.95
          },
          {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 0.5,
            stagger: 0.1,
            delay: 0.8,
            ease: "power2.out"
          }
        );
      }

    }, formRef);

    return () => ctx.revert();
  }, [isLoadingSections, sections.length]);

  useEffect(() => {
    if (watchedTestType === "simulation") {
      setValue("num_questions", 120);
      setValue("num_sections", 5);
    } else {
      setValue("num_questions", 25);
      setValue("num_sections", 3);
    }
  }, [watchedTestType, setValue]);

  const handleMainSectionChange = (
    section: LearningSection,
    isChecked: boolean
  ) => {
    const currentSubsections = watchedSubsections || [];
    const sectionSlugs = section.subsections.map(sub => sub.slug);
    
    if (isChecked) {
      // Add all subsections from this section
      const newSubsections = [...new Set([...currentSubsections, ...sectionSlugs])];
      setValue("subsections", newSubsections, { shouldValidate: true });
    } else {
      // Remove all subsections from this section
      const newSubsections = currentSubsections.filter(slug => !sectionSlugs.includes(slug));
      setValue("subsections", newSubsections, { shouldValidate: true });
    }
  };

  const handleSubsectionToggle = (subsectionSlug: string) => {
    const currentSubsections = watchedSubsections || [];
    const newSubsections = currentSubsections.includes(subsectionSlug)
      ? currentSubsections.filter(s => s !== subsectionSlug)
      : [...currentSubsections, subsectionSlug];
    setValue("subsections", newSubsections, { shouldValidate: true });
  };

  const startTestMutation = useMutation({
    mutationFn: startPracticeSimulationTest,
    onSuccess: (data) => {
      toast.success(t("api.startSuccess"));
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });
      
      // Animate out before navigation
      gsap.to(formRef.current, {
        opacity: 0,
        scale: 0.95,
        y: -20,
        duration: 0.3,
        ease: "power2.in",
        onComplete: () => {
          router.push(PATHS.STUDY.TESTS.ATTEMPT(data.attempt_id));
        }
      });
    },
    onError: (error) => {
      const errorMessage = getApiErrorMessage(error, commonT("errors.generic"));
      toast.error(errorMessage, {
        duration: 8000,
      });
      
      // Shake animation on error
      gsap.to(formRef.current, {
        x: 0,
        duration: 0.5,
        ease: "power2.inOut",
        keyframes: [
          { x: -10 },
          { x: 10 },
          { x: -10 },
          { x: 10 },
          { x: 0 }
        ]
      });
    },
  });

  const onSubmit = (formData: FormValues) => {
    const payload: any = {
      test_type: formData.test_type,
      config: {
        subsections: formData.subsections,
        num_questions: formData.num_questions,
        num_sections: formData.num_sections,
        starred: formData.starred,
        not_mastered: formData.not_mastered,
      },
    };
    startTestMutation.mutate(payload);
  };

  if (isLoadingSections) return <StartTestFormSkeleton />;

  return (
    <form ref={formRef} onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      {sectionsError && (
        <Alert variant="destructive" className="animate-fade-in">
          <AlertTitle>{commonT("errors.requestFailed")}</AlertTitle>
          <AlertDescription>
            {getApiErrorMessage(sectionsError, commonT("errors.generic"))}
          </AlertDescription>
        </Alert>
      )}

      {/* Test Type Selection Card */}
      <Card ref={settingsCardRef}>
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
                  value={field.value}
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
        </CardContent>
      </Card>

      {/* Sections Selection Card - Code 1 Design */}
      <Card ref={sectionsCardRef} className="overflow-hidden w-full max-w-none border-2 dark:bg-[#0B1739] dark:border-[#7E89AC]">
       
        <CardContent className="space-y-6">
          {errors.subsections && (
            <p className="text-sm font-medium text-destructive animate-pulse">
              {errors.subsections.message}
            </p>
          )}

          <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-6">
            {sections.map((section, index) => {
              const sectionSlugs = section.subsections.map(sub => sub.slug);
              const allSubSelected = sectionSlugs.every(slug => 
                watchedSubsections?.includes(slug)
              );
              const someSubSelected = sectionSlugs.some(slug => 
                watchedSubsections?.includes(slug)
              );
              const isSectionSelected = allSubSelected;
              const isPartiallySelected = someSubSelected && !allSubSelected;

              return (
                <div
                  key={section.slug}
                  ref={(el) => {
                    sectionCardsRef.current[index] = el;
                  }}
                  className={cn(
                    "w-full max-w-full rounded-2xl border-2 p-6 shadow-md transition-all duration-200",
                    isSectionSelected
                      ? "border-primary bg-primary/5 dark:bg-[#074182]/50"
                      : isPartiallySelected
                      ? "border-primary/50 bg-primary/2 dark:bg-[#074182]/20"
                      : "border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500"
                  )}
                >
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div className="flex items-center space-x-3 gap-2 rtl:space-x-reverse">
                      <Checkbox
                        id={`section-${section.slug}`}
                        checked={isSectionSelected}
                        data-state={isPartiallySelected ? "indeterminate" : isSectionSelected ? "checked" : "unchecked"}
                        onCheckedChange={(checked) =>
                          handleMainSectionChange(section, checked === true)
                        }
                        className={
                          isPartiallySelected
                            ? "data-[state=indeterminate]:bg-primary data-[state=indeterminate]:border-primary data-[state=indeterminate]:text-primary-foreground"
                            : ""
                        }
                        aria-label={`Select all in ${section.name}`}
                      >
                        {isPartiallySelected && (
                          <Minus className="h-4 w-4" />
                        )}
                      </Checkbox>
                      <h3 className="font-semibold text-lg sm:text-xl">
                        {section.name}
                      </h3>
                    </div>
                    <div
                      className={cn(
                        "flex-shrink-0 h-6 w-6 rounded-full border-2 flex items-center justify-center transition-all",
                        isSectionSelected
                          ? "bg-primary border-primary text-primary-foreground"
                          : isPartiallySelected
                          ? "bg-primary/50 border-primary text-primary-foreground"
                          : "bg-transparent border-muted-foreground"
                      )}
                      aria-hidden="true"
                    >
                      {isSectionSelected && <Check className="h-4 w-4" />}
                      {isPartiallySelected && !isSectionSelected && <Minus className="h-3 w-3" />}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {section.subsections.map((subsection) => {
                      const isSubsectionSelected = watchedSubsections?.includes(subsection.slug) || false;
                      
                      return (
                        <button
                          key={subsection.slug}
                          type="button"
                          onClick={() => handleSubsectionToggle(subsection.slug)}
                          className={cn(
                            "rounded-lg p-3 text-center flex justify-center items-center text-sm select-none border transition-all duration-200 cursor-pointer",
                            isSubsectionSelected
                              ? "border-primary/50 bg-primary/10 font-medium text-primary"
                              : "border-gray-300 dark:border-gray-600 bg-muted/50 text-muted-foreground hover:border-primary/50 hover:bg-primary/5"
                          )}
                        >
                          {subsection.name}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Options Card - Keep Code 2 Design */}
      <Card ref={optionsCardRef}>
      
        <CardContent className="space-y-6">
          
          {/* Number of Sections Field */}
          <div>
            <Label htmlFor="num_sections" className="text-base font-medium">
              عدد الأقسام
            </Label>
            <Controller
              name="num_sections"
              control={control}
              render={({ field, fieldState }) => (
                <>
                  <Input
                    id="num_sections"
                    type="number"
                    value={field.value}
                    onChange={(e) => {
                      if (watchedTestType !== "simulation") {
                        field.onChange(parseInt(e.target.value, 10) || 0)
                      }
                    }}
                    disabled={watchedTestType === "simulation"}
                    className="mt-2"
                    min="1"
                    max="10"
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

          {/* Number of Questions Field */}
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
                    value={field.value}
                    onChange={(e) => {
                      if (watchedTestType !== "simulation") {
                        field.onChange(parseInt(e.target.value, 10) || 0)
                      }
                    }}
                    disabled={watchedTestType === "simulation"}
                    className="mt-2"
                    min="5"
                    max="150"
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

          {/* Starred and Not Mastered Switches */}
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

      <div ref={submitButtonRef} className="flex ltr:justify-end rtl:justify-start">
        <Button
          type="submit"
          disabled={startTestMutation.isPending || !isValid}
          size="lg"
          className="text-white"
        >
          {startTestMutation.isPending && (
            <Loader2 className="me-2 h-5 w-5 animate-spin" />
          )}
          {startTestMutation.isPending ? commonT("loading") : t("submit")}
        </Button>
      </div>
    </form>
  );
};

const StartTestFormSkeleton: React.FC = () => {
  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <Skeleton className="mb-2 h-7 w-3/5" />
          <Skeleton className="h-4 w-4/5" />
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Skeleton className="mb-2 h-5 w-24" />
            <div className="mt-2 grid grid-cols-2 gap-2">
              <Skeleton className="h-10 rounded-md" />
              <Skeleton className="h-10 rounded-md" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="overflow-hidden w-full max-w-none border-2">
        <CardHeader>
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-4 w-2/3" />
        </CardHeader>
        <CardContent className="space-y-3 p-6">
          <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-6">
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
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <Skeleton className="mb-2 h-7 w-3/5" />
          <Skeleton className="h-4 w-4/5" />
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Skeleton className="mb-2 h-6 w-1/4" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div>
            <Skeleton className="mb-2 h-6 w-1/4" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div className="space-y-4">
            <div className="flex items-center space-x-2 rounded-md border p-3 rtl:space-x-reverse">
              <Skeleton className="h-6 w-10 rounded-full" />
              <Skeleton className="h-4 w-48 flex-1" />
            </div>
            <div className="flex items-center space-x-2 rounded-md border p-3 rtl:space-x-reverse">
              <Skeleton className="h-6 w-10 rounded-full" />
              <Skeleton className="h-4 w-48 flex-1" />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex ltr:justify-end rtl:justify-start">
        <Skeleton className="h-12 w-32" />
      </div>
    </div>
  );
};

export default StartTestForm;
