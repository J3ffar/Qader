"use client";

import React, { ReactNode, useEffect, useRef } from "react";
import { useForm, Controller, FieldError } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Loader2, Minus, Sparkles, Check } from "lucide-react";
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
import { Switch } from "@/components/ui/switch";
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
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface FormValues {
  selectedSubsections: Record<string, boolean>;
  num_questions: number;
  starred: boolean;
  not_mastered: boolean;
}

const FormSkeleton = () => {
  const t = useTranslations("Common");
  return (
    <div className="mx-auto max-w-4xl space-y-8 animate-pulse">
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
      <Card className="overflow-hidden w-full max-w-none border-2">
        <CardHeader>
          <Skeleton className="h-8 w-1/4" />
          <Skeleton className="h-4 w-1/2" />
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
      <div className="flex justify-center">
        <Button disabled size="lg" className="w-full max-w-md">
          <Loader2 className="me-2 h-5 w-5 animate-spin" />
          {t("loading")}
        </Button>
      </div>
    </div>
  );
};

const TraditionalLearningConfigForm: React.FC = () => {
  const t = useTranslations("Study.traditionalLearning.config");
  const commonT = useTranslations("Common");
  const router = useRouter();
  const queryClient = useQueryClient();

  // Refs for GSAP animations
  const formRef = useRef<HTMLFormElement>(null);
  const sectionsCardRef = useRef<HTMLDivElement>(null);
  const optionsCardRef = useRef<HTMLDivElement>(null);
  const submitButtonRef = useRef<HTMLDivElement>(null);
  const sectionCardsRef = useRef<(HTMLDivElement | null)[]>([]);
  const optionItemsRef = useRef<(HTMLDivElement | null)[]>([]);

  const {
    data: learningSectionsData,
    error: sectionsError,
    isLoading: isSectionsLoading,
  } = useQuery({
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

  // GSAP Animation Effect
  useEffect(() => {
    if (!formRef.current || isSectionsLoading) return;

    const ctx = gsap.context(() => {
      // Create main timeline
      const mainTl = gsap.timeline({
        defaults: {
          ease: "power3.out",
        }
      });

      // Set initial states
      gsap.set([
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
        .to(sectionsCardRef.current, {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.6,
        })
        .to(optionsCardRef.current, {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.6,
        }, "-=0.4") // Overlap animations
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
            delay: 0.3,
            ease: "power2.out"
          }
        );
      }

      // Animate option cards with a bounce effect
      const validOptionItems = optionItemsRef.current.filter(item => item !== null);
      if (validOptionItems.length > 0) {
        gsap.fromTo(
          validOptionItems,
          {
            opacity: 0,
            y: 20,
            rotateX: -15,
          },
          {
            opacity: 1,
            y: 0,
            rotateX: 0,
            duration: 0.5,
            stagger: 0.1,
            delay: 0.8,
            ease: "back.out(1.5)"
          }
        );
      }

      // Add hover animations for interactive elements
      validSectionCards.forEach(item => {
        if (!item) return;
        
        item.addEventListener('mouseenter', () => {
          gsap.to(item, {
            scale: 1.02,
            duration: 0.2,
            ease: "power2.out"
          });
        });
        
        item.addEventListener('mouseleave', () => {
          gsap.to(item, {
            scale: 1,
            duration: 0.2,
            ease: "power2.out"
          });
        });
      });

      // Pulse animation for submit button
      gsap.to(submitButtonRef.current, {
        scale: 1.05,
        duration: 0.6,
        repeat: 2,
        yoyo: true,
        delay: 1.5,
        ease: "power1.inOut"
      });

    }, formRef);

    return () => ctx.revert();
  }, [isSectionsLoading, sections.length]);

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

      // Animate out before navigation
      gsap.to(formRef.current, {
        opacity: 0,
        scale: 0.95,
        y: -20,
        duration: 0.3,
        ease: "power2.in",
        onComplete: () => {
          router.push(PATHS.STUDY.TRADITIONAL_LEARNING.SESSION(data.attempt_id));
        }
      });
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, t("api.startError")));
      
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

  if (isSectionsLoading) {
    return <FormSkeleton />;
  }

  if (sectionsError) {
    return (
      <Alert variant="destructive" className="animate-fade-in">
        <AlertTitle>{commonT("errors.fetchFailedTitle")}</AlertTitle>
        <AlertDescription>
          {getApiErrorMessage(sectionsError, t("api.startError"))}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <form
      ref={formRef}
      onSubmit={handleSubmit(onSubmit)}
      className="mx-auto max-w-4xl space-y-8"
    >
      <Card 
        ref={sectionsCardRef}
        className="overflow-hidden w-full max-w-none border-2 dark:bg-[#0B1739] dark:border-[#7E89AC]"
      >
        <CardHeader>
          <CardTitle>{t("sectionsTitle")}</CardTitle>
          <CardDescription>{t("sectionsDescription")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {errors.selectedSubsections && (
            <p className="text-sm font-medium text-destructive animate-pulse">
              {errors.selectedSubsections.message as ReactNode}
            </p>
          )}

          <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-6">
            {sections.map((section, index) => {
              const allSubSelected = section.subsections.every(
                (sub) => selectedSubsectionsWatched[sub.slug]
              );
              const someSubSelected = section.subsections.some(
                (sub) => selectedSubsectionsWatched[sub.slug]
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
                      const isSubsectionSelected = selectedSubsectionsWatched[subsection.slug] || false;
                      
                      return (
                        <Controller
                          key={subsection.slug}
                          name={`selectedSubsections.${subsection.slug}`}
                          control={control}
                          defaultValue={false}
                          render={({ field }) => (
                            <button
                              type="button"
                              onClick={() => field.onChange(!field.value)}
                              className={cn(
                                "rounded-lg p-3 text-center flex justify-center items-center text-sm select-none border transition-all duration-200 cursor-pointer",
                                isSubsectionSelected
                                  ? "border-primary/50 bg-primary/10 font-medium text-primary"
                                  : "border-gray-300 dark:border-gray-600 bg-muted/50 text-muted-foreground hover:border-primary/50 hover:bg-primary/5"
                              )}
                            >
                              {subsection.name}
                            </button>
                          )}
                        />
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card 
        ref={optionsCardRef}
        className="overflow-hidden w-full max-w-none border-2 dark:bg-[#0B1739] dark:border-[#7E89AC]"
      >
        <CardHeader>
          <CardTitle>{t("advancedOptionsTitle")}</CardTitle>
          <CardDescription>{t("advancedOptionsDescription")}</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div 
            ref={(el) => {
              optionItemsRef.current[0] = el;
            }}
            className="flex flex-col items-center justify-between p-7 rounded-lg border option-card"
          >
            <Label
              htmlFor="num_questions"
              className="text-base font-medium justify-center"
            >
              {t("numQuestionsLabel")}
            </Label>
            <Controller
              name="num_questions"
              control={control}
              render={({ field }) => (
                <div className="mt-2 flex justify-center items-center gap-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={(e) => {
                      field.onChange(Math.max((field.value || 0) - 1, 1));
                      // Add a little bounce animation
                      const target = e.currentTarget;
                      if (target) {
                        gsap.to(target, {
                          scale: 0.9,
                          duration: 0.1,
                          yoyo: true,
                          repeat: 1
                        });
                      }
                    }}
                    className="w-10 h-10 p-0 text-xl cursor-pointer transition-transform"
                  >
                    –
                  </Button>

                  <input
                    type="text"
                    value={field.value || ""}
                    onChange={(e) => {
                      const value = parseInt(e.target.value, 10);
                      field.onChange(isNaN(value) ? "" : Math.max(value, 1));
                    }}
                    onBlur={() => {
                      // Validate on blur to clamp value between 1 and 50
                      const value = Math.max(1, Math.min(50, field.value || 20));
                      field.onChange(value);
                    }}
                    className="w-16 text-center text-lg font-semibold border rounded-md px-2 py-1 dark:bg-transparent dark:border-gray-600"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={(e) => {
                      field.onChange(Math.min((field.value || 0) + 1, 50));
                      // Add a little bounce animation
                      const target = e.currentTarget;
                      if (target) {
                        gsap.to(target, {
                          scale: 0.9,
                          duration: 0.1,
                          yoyo: true,
                          repeat: 1
                        });
                      }
                    }}
                    className="w-10 h-10 p-0 text-xl cursor-pointer transition-transform"
                  >
                    +
                  </Button>
                </div>
              )}
            />

            {errors.num_questions && (
              <p className="mt-1 text-sm font-medium text-destructive animate-pulse">
                {errors.num_questions.message}
              </p>
            )}
          </div>
          
          <Controller
            name="starred"
            control={control}
            render={({ field }) => (
              <div 
                ref={(el) => {
                  optionItemsRef.current[1] = el;
                }}
                className="flex items-center justify-between md:space-x-8 rounded-lg border p-7 rtl:space-x-reverse option-card"
              >
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
              <div 
                ref={(el) => {
                  optionItemsRef.current[2] = el;
                }}
                className="flex items-center justify-between md:space-x-8 rounded-lg border p-7 rtl:space-x-reverse option-card"
              >
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
        </CardContent>
      </Card>

      <div ref={submitButtonRef} className="flex justify-center">
        <Button
          type="submit"
          disabled={startPracticeMutation.isPending || !isValid}
          size="lg"
          className="w-full max-w-md transform transition-all duration-200 hover:scale-105"
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
