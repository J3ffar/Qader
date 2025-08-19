"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Award, Flame, HelpCircle, Target } from "lucide-react";
import { useTranslations } from "next-intl";
import type { UserStatistics } from "@/types/api/study.types";

interface Props {
  overallStats: UserStatistics["overall"];
}

export function OverallStatsCards({ overallStats }: Props) {
  const t = useTranslations("Study.statistics.cards");
  const { mastery_level, study_streaks, activity_summary } = overallStats;
  const containerRef = useRef<HTMLDivElement>(null);
  const cardsRef = useRef<(HTMLDivElement | null)[]>([]);
  const hasAnimated = useRef(false);

  const cardsData = [
    {
      title: t("verbalMastery"),
      value:
        mastery_level.verbal != null
          ? `${mastery_level.verbal.toFixed(1)}%`
          : "N/A",
      description: t("currentLevel"),
      icon: Target,
      gradient: "from-emerald-500 to-teal-600",
      bgColor: "bg-gradient-to-br from-emerald-50 to-teal-50",
      iconBg: "bg-emerald-100",
      iconColor: "text-emerald-600",
      valueColor: "text-emerald-700",
      borderColor: "border-emerald-200",
    },
    {
      title: t("quantMastery"),
      value:
        mastery_level.quantitative != null
          ? `${mastery_level.quantitative.toFixed(1)}%`
          : "N/A",
      description: t("currentLevel"),
      icon: Activity,
      gradient: "from-blue-500 to-indigo-600",
      bgColor: "bg-gradient-to-br from-blue-50 to-indigo-50",
      iconBg: "bg-blue-100",
      iconColor: "text-blue-600",
      valueColor: "text-blue-700",
      borderColor: "border-blue-200",
    },
    {
      title: t("studyStreak"),
      value: study_streaks.current_days,
      description: t("longestStreak", { count: study_streaks.longest_days }),
      icon: Flame,
      gradient: "from-orange-500 to-red-500",
      bgColor: "bg-gradient-to-br from-orange-50 to-red-50",
      iconBg: "bg-orange-100",
      iconColor: "text-orange-600",
      valueColor: "text-orange-700",
      borderColor: "border-orange-200",
    },
    {
      title: t("questionsAnswered"),
      value: `+${activity_summary.total_questions_answered}`,
      description: t("totalThisPeriod"),
      icon: HelpCircle,
      gradient: "from-purple-500 to-pink-600",
      bgColor: "bg-gradient-to-br from-purple-50 to-pink-50",
      iconBg: "bg-purple-100",
      iconColor: "text-purple-600",
      valueColor: "text-purple-700",
      borderColor: "border-purple-200",
    },
    {
      title: t("testsCompleted"),
      value: `+${activity_summary.total_tests_completed}`,
      description: t("totalThisPeriod"),
      icon: Award,
      gradient: "from-amber-500 to-yellow-600",
      bgColor: "bg-gradient-to-br from-amber-50 to-yellow-50",
      iconBg: "bg-amber-100",
      iconColor: "text-amber-600",
      valueColor: "text-amber-700",
      borderColor: "border-amber-200",
    },
  ];

  useEffect(() => {
    if (!containerRef.current || hasAnimated.current) return;
    hasAnimated.current = true;

    const ctx = gsap.context(() => {
      // Set initial state for all cards
      gsap.set(cardsRef.current, {
        opacity: 0,
        y: 40,
        scale: 0.9,
        rotationX: -10,
      });

      // Create timeline for sequential animations
      const tl = gsap.timeline({
        defaults: {
          duration: 0.6,
          ease: "back.out(1.4)",
        }
      });

      // Animate cards with stagger effect
      tl.to(cardsRef.current, {
        opacity: 1,
        y: 0,
        scale: 1,
        rotationX: 0,
        stagger: {
          amount: 0.5,
          from: "start",
          ease: "power2.inOut"
        },
        onComplete: function() {
          // Add subtle floating animation after main animation
          cardsRef.current.forEach((card, index) => {
            if (card) {
              gsap.to(card, {
                y: -2,
                duration: 2,
                ease: "power1.inOut",
                yoyo: true,
                repeat: -1,
                delay: index * 0.1,
              });
            }
          });
        }
      });

      // Animate gradient bars
      const gradientBars:any = containerRef.current?.querySelectorAll('.gradient-bar');
      tl.fromTo(gradientBars, 
        {
          scaleX: 0,
          transformOrigin: "left center",
        },
        {
          scaleX: 1,
          duration: 0.8,
          stagger: 0.1,
          ease: "power3.out",
        }, 
        "-=0.4"
      );

      // Animate icons
      const icons:any = containerRef.current?.querySelectorAll('.icon-container');
      tl.fromTo(icons,
        {
          scale: 0,
          rotation: -180,
        },
        {
          scale: 1,
          rotation: 0,
          duration: 0.5,
          stagger: 0.08,
          ease: "back.out(2)",
        },
        "-=0.6"
      );

      // Animate values with counting effect
      const values = containerRef.current?.querySelectorAll('.card-value');
      values?.forEach((valueEl, index) => {
        const el = valueEl as HTMLElement;
        const finalText = el.innerText;
        const isPercentage = finalText.includes('%');
        const isNumber = finalText.includes('+');
        
        if (isPercentage) {
          const numValue = parseFloat(finalText);
          if (!isNaN(numValue)) {
            gsap.fromTo(el, 
              { 
                innerText: 0,
              },
              {
                innerText: numValue,
                duration: 1.5,
                delay: 0.3 + (index * 0.1),
                ease: "power2.out",
                snap: { innerText: 0.1 },
                onUpdate: function() {
                  el.innerText = `${parseFloat(el.innerText).toFixed(1)}%`;
                }
              }
            );
          }
        } else if (isNumber) {
          const numValue = parseInt(finalText.replace('+', ''));
          if (!isNaN(numValue)) {
            gsap.fromTo(el,
              { 
                innerText: 0,
              },
              {
                innerText: numValue,
                duration: 1.5,
                delay: 0.3 + (index * 0.1),
                ease: "power2.out",
                snap: { innerText: 1 },
                onUpdate: function() {
                  el.innerText = `+${Math.round(parseFloat(el.innerText))}`;
                }
              }
            );
          }
        } else if (!isNaN(parseInt(finalText))) {
          const numValue = parseInt(finalText);
          gsap.fromTo(el,
            { 
              innerText: 0,
            },
            {
              innerText: numValue,
              duration: 1.5,
              delay: 0.3 + (index * 0.1),
              ease: "power2.out",
              snap: { innerText: 1 },
            }
          );
        }
      });

      // Animate descriptions with fade in
      const descriptions:any = containerRef.current?.querySelectorAll('.card-description');
      tl.fromTo(descriptions,
        {
          opacity: 0,
          y: 10,
        },
        {
          opacity: 1,
          y: 0,
          duration: 0.4,
          stagger: 0.05,
          ease: "power2.out",
        },
        "-=0.8"
      );

    }, containerRef);

    return () => {
      ctx.revert();
    };
  }, [overallStats]);

  return (
    <div 
      ref={containerRef}
      className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-5 bg-transparent shadow-none"
    >
      {cardsData.map((card, index) => (
        <Card 
          key={index}
          ref={(el:any) => (cardsRef.current[index] = el)}
          className={`relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 ${card.bgColor} ${card.borderColor} border-2`}
          style={{ transformStyle: 'preserve-3d' }}
        >
          {/* Gradient accent bar */}
          <div className={`gradient-bar absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${card.gradient}`} />
          
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-medium text-gray-700">
              {card.title}
            </CardTitle>
            <div className={`icon-container p-2 rounded-full ${card.iconBg}`}>
              <card.icon className={`h-5 w-5 ${card.iconColor}`} />
            </div>
          </CardHeader>
          
          <CardContent>
            <div className={`card-value text-2xl font-bold ${card.valueColor} mb-1`}>
              {card.value}
            </div>
            <p className="card-description text-xs text-gray-600">
              {card.description}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
