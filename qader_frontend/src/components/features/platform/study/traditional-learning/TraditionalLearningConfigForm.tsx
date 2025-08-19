"use client";

import React, { ReactNode, useEffect, useRef } from "react";
import { useForm, Controller, FieldError } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Loader2, Minus, Sparkles } from "lucide-react";
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
import { Skeleton } from "@/components/ui/skeleton";

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
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
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
  const accordionItemsRef = useRef<(HTMLDivElement | null)[]>([]);
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

      // Animate accordion items with stagger
      const validAccordionItems = accordionItemsRef.current.filter(item => item !== null);
      if (validAccordionItems.length > 0) {
        gsap.fromTo(
          validAccordionItems,
          {
            opacity: 0,
            x: -30,
            scale: 0.95
          },
          {
            opacity: 1,
            x: 0,
            scale: 1,
            duration: 0.4,
            stagger: 0.08,
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
      validAccordionItems.forEach(item => {
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
      
      // Shake animation on error - Fixed: using single number instead of array
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
        <CardContent>
          {errors.selectedSubsections && (
            <p className="mb-4 text-sm font-medium text-destructive animate-pulse">
              {errors.selectedSubsections.message as ReactNode}
            </p>
          )}
          <Accordion
            type="multiple"
            defaultValue={sections.map((s) => s.slug)}
            className="w-full space-y-3 grid lg:grid-cols-2 grid-cols-1 gap-3"
          >
            {sections.map((section, index) => {
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
                  ref={(el) => {
                    accordionItemsRef.current[index] = el;
                  }}
                  value={section.slug}
                  key={section.slug}
                  className="rounded-lg border accordion-item"
                >
                  <AccordionTrigger className="p-4 hover:no-underline">
                    <div className="flex items-center space-x-3 gap-2 rtl:space-x-reverse">
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
                        className="cursor-pointer font-bold"
                      >
                        {section.name}
                      </label>
                    </div>
                  </AccordionTrigger>

                  <AccordionContent className="grid grid-cols-2 gap-x-8 gap-y-3 p-4 pt-0">
                    {section.subsections.map((sub) => (
                      <Controller
                        key={sub.slug}
                        name={`selectedSubsections.${sub.slug}`}
                        control={control}
                        defaultValue={false}
                        render={({ field }) => (
                          <button
                            type="button"
                            onClick={() => field.onChange(!field.value)}
                            className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all duration-200 cursor-pointer transform hover:scale-105 ${
                              field.value
                                ? "bg-primary text-white border-primary shadow-lg"
                                : "border border-gray-300 hover:border-primary font-normal hover:shadow-md"
                            }`}
                          >
                            {sub.name}
                          </button>
                        )}
                      />
                    ))}
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>
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
                      field.onChange(Math.max((field.value || 0) - 1, 0));
                      // Add a little bounce animation - Fixed: proper type checking
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
                      field.onChange(isNaN(value) ? "" : Math.max(value, 0));
                    }}
                    className="w-16 text-center text-lg font-semibold border rounded px-2 py-1"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={(e) => {
                      field.onChange((field.value || 0) + 1);
                      // Add a little bounce animation - Fixed: proper type checking
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
