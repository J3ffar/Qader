import React, { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Flame, Star, TrendingUp, Zap } from "lucide-react";
import { useTranslations } from "next-intl";
import { gsap } from "gsap";

interface QuickStatsProps {
  points: number;
  currentStreakDays: number;
}

export const QuickStats: React.FC<QuickStatsProps> = ({
  points,
  currentStreakDays,
}) => {
  const t = useTranslations("Study.StudyPage.dashboard.quickStats");
  const containerRef = useRef<HTMLDivElement>(null);
  const pointsCardRef = useRef<HTMLDivElement>(null);
  const streakCardRef = useRef<HTMLDivElement>(null);
  const pointsNumberRef = useRef<HTMLDivElement>(null);
  const streakNumberRef = useRef<HTMLDivElement>(null);
  const pointsIconRef = useRef<HTMLDivElement>(null);
  const streakIconRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const tl = gsap.timeline({ delay: 0 }); // Start immediately on page load

    // Set initial states - completely hidden
    gsap.set([pointsCardRef.current, streakCardRef.current], {
      y: 80,
      opacity: 0,
      scale: 0.8,
      rotateX: -15,
    });

    gsap.set([pointsNumberRef.current, streakNumberRef.current], {
      scale: 0,
      rotation: -180,
    });

    gsap.set([pointsIconRef.current, streakIconRef.current], {
      scale: 0,
      rotation: -360,
      transformOrigin: "center center",
    });

    // Animate cards entrance with stagger
    tl.to([pointsCardRef.current, streakCardRef.current], {
      duration: 0.8,
      y: 0,
      opacity: 1,
      scale: 1,
      rotateX: 0,
      stagger: 0.1,
      ease: "back.out(1.4)",
    })
    
    // Animate icons
    .to([pointsIconRef.current, streakIconRef.current], {
      duration: 0.6,
      scale: 1,
      rotation: 0,
      stagger: 0.1,
      ease: "elastic.out(1, 0.5)",
    }, "-=0.5")
    
    // Animate numbers
    .to([pointsNumberRef.current, streakNumberRef.current], {
      duration: 0.7,
      scale: 1,
      rotation: 0,
      stagger: 0.1,
      ease: "back.out(1.8)",
    }, "-=0.4");

    // Add floating animation for icons after entrance
    gsap.to(pointsIconRef.current, {
      y: -3,
      duration: 2,
      yoyo: true,
      repeat: -1,
      ease: "power2.inOut",
      delay: 1.5,
    });

    gsap.to(streakIconRef.current, {
      y: -4,
      rotation: 5,
      duration: 2.5,
      yoyo: true,
      repeat: -1,
      ease: "power2.inOut",
      delay: 1.7,
    });

    // Animate counter numbers
    let pointsObj = { value: 0 };
    let streakObj = { value: 0 };

    gsap.to(pointsObj, {
      value: points,
      duration: 1.2,
      delay: 0.8,
      ease: "power2.out",
      onUpdate: () => {
        if (pointsNumberRef.current) {
          pointsNumberRef.current.textContent = Math.floor(pointsObj.value).toLocaleString();
        }
      },
    });

    gsap.to(streakObj, {
      value: currentStreakDays,
      duration: 1.0,
      delay: 0.9,
      ease: "power2.out",
      onUpdate: () => {
        if (streakNumberRef.current) {
          streakNumberRef.current.textContent = `${Math.floor(streakObj.value)} ${t("days")}`;
        }
      },
    });

  }, [points, currentStreakDays, t]);

  return (
    <div ref={containerRef} className="grid gap-4 md:grid-cols-2">
      {/* Points Card */}
      <Card 
        ref={pointsCardRef}
        className="group relative overflow-hidden border-0 bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 shadow-sm transition-all duration-300 hover:shadow-2xl hover:shadow-yellow-500/25 hover:-translate-y-1 hover:scale-[1.02] dark:from-amber-950/20 dark:via-yellow-950/20 dark:to-orange-950/20"
      >
        {/* Animated background glow */}
        <div className="absolute -top-4 -right-4 h-24 w-24 rounded-full bg-gradient-to-br from-yellow-400 to-amber-500 opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-20" />
        <div className="absolute -bottom-4 -left-4 h-32 w-32 rounded-full bg-gradient-to-br from-orange-400 to-yellow-500 opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-10" />
        
        <CardHeader className="relative flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-amber-800 transition-colors group-hover:text-amber-900 dark:text-amber-200 dark:group-hover:text-amber-100">
            {t("pointsTitle")}
          </CardTitle>
          <div ref={pointsIconRef} className="relative">
            <Star className="h-6 w-6 text-yellow-500 transition-all duration-300 group-hover:text-yellow-400 group-hover:scale-110 group-hover:rotate-12" />
            <div className="absolute inset-0 h-6 w-6 rounded-full bg-yellow-400 opacity-0 blur-md transition-opacity duration-300 group-hover:opacity-30" />
          </div>
        </CardHeader>
        <CardContent className="relative">
          <div 
            ref={pointsNumberRef}
            className="text-3xl font-bold text-amber-900 transition-all duration-300 group-hover:text-amber-800 group-hover:scale-105 dark:text-amber-100 dark:group-hover:text-amber-50"
          >
            0
          </div>
          <p className="text-xs text-amber-600/80 transition-colors group-hover:text-amber-700 dark:text-amber-300/80 dark:group-hover:text-amber-200">
            {t("pointsSubtitle")}
          </p>
          {/* Floating particles effect */}
          <div className="absolute top-4 right-8 h-1 w-1 rounded-full bg-yellow-400 opacity-0 transition-all duration-700 group-hover:opacity-60 group-hover:translate-y-2" />
          <div className="absolute top-8 right-12 h-1 w-1 rounded-full bg-amber-400 opacity-0 transition-all duration-1000 group-hover:opacity-40 group-hover:translate-y-3" />
        </CardContent>
      </Card>

      {/* Streak Card */}
      <Card 
        ref={streakCardRef}
        className="group relative overflow-hidden border-0 bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 shadow-sm transition-all duration-300 hover:shadow-2xl hover:shadow-orange-500/25 hover:-translate-y-1 hover:scale-[1.02] dark:from-orange-950/20 dark:via-red-950/20 dark:to-pink-950/20"
      >
        {/* Animated background glow */}
        <div className="absolute -top-4 -right-4 h-24 w-24 rounded-full bg-gradient-to-br from-orange-400 to-red-500 opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-20" />
        <div className="absolute -bottom-4 -left-4 h-32 w-32 rounded-full bg-gradient-to-br from-red-400 to-pink-500 opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-10" />
        
        <CardHeader className="relative flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-orange-800 transition-colors group-hover:text-orange-900 dark:text-orange-200 dark:group-hover:text-orange-100">
            {t("streakTitle")}
          </CardTitle>
          <div ref={streakIconRef} className="relative">
            <Flame className="h-6 w-6 text-orange-500 transition-all duration-300 group-hover:text-orange-400 group-hover:scale-110 group-hover:rotate-12" />
            <div className="absolute inset-0 h-6 w-6 rounded-full bg-orange-400 opacity-0 blur-md transition-opacity duration-300 group-hover:opacity-40" />
            {/* Fire flicker effect */}
            <Zap className="absolute -top-1 -right-1 h-3 w-3 text-yellow-400 opacity-0 transition-all duration-500 group-hover:opacity-80 group-hover:scale-125" />
          </div>
        </CardHeader>
        <CardContent className="relative">
          <div 
            ref={streakNumberRef}
            className="text-3xl font-bold text-orange-900 transition-all duration-300 group-hover:text-orange-800 group-hover:scale-105 dark:text-orange-100 dark:group-hover:text-orange-50"
          >
            0 {t("days")}
          </div>
          <p className="text-xs text-orange-600/80 transition-colors group-hover:text-orange-700 dark:text-orange-300/80 dark:group-hover:text-orange-200">
            {t("streakSubtitle")}
          </p>
          {/* Heat wave effect */}
          <div className="absolute bottom-4 right-8 h-1 w-1 rounded-full bg-orange-400 opacity-0 transition-all duration-700 group-hover:opacity-70 group-hover:translate-y-1" />
          <div className="absolute bottom-6 right-6 h-1 w-1 rounded-full bg-red-400 opacity-0 transition-all duration-900 group-hover:opacity-50 group-hover:translate-y-2" />
          <div className="absolute bottom-8 right-10 h-1 w-1 rounded-full bg-pink-400 opacity-0 transition-all duration-1100 group-hover:opacity-30 group-hover:translate-y-3" />
        </CardContent>
      </Card>
    </div>
  );
};
