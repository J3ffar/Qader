"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { UserStatistics } from "@/types/api/study.types";
import { PerformanceTrendsChart } from "./PerformanceTrendsChart";
import { SectionPerformanceBreakdown } from "./SectionPerformanceBreakdown";
import { OverallStatsCards } from "./OverallStatsCards";
import { TimeAnalyticsCard } from "./TimeAnalyticsCard";
import { AverageScoresByTypeCard } from "./AverageScoresByTypeCard";
import { ActionableInsightsTabs } from "./ActionableInsightsTabs";

interface StatisticsViewProps {
  statistics: UserStatistics;
}

/**
 * A purely presentational component for displaying user statistics with GSAP animations.
 * It accepts the full statistics object as a prop and handles the layout.
 * This component is reused by both the student-facing dashboard and the admin panel.
 */
export function StatisticsView({ statistics }: StatisticsViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const statsCardsRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const row3Refs = useRef<HTMLDivElement[]>([]);
  const row4Refs = useRef<HTMLDivElement[]>([]);
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!containerRef.current || hasAnimated.current) return;
    hasAnimated.current = true;

    const ctx = gsap.context(() => {
      // Set initial states with more subtle transformations
      gsap.set([statsCardsRef.current], {
        opacity: 0,
        y: 20,
        scale: 0.98,
      });

      gsap.set([chartRef.current], {
        opacity: 0,
        y: 25,
        scale: 0.97,
      });

      gsap.set(row3Refs.current, {
        opacity: 0,
        y: 30,
        scale: 0.96,
      });

      gsap.set(row4Refs.current, {
        opacity: 0,
        y: 35,
        scale: 0.95,
      });

      // Create main timeline with smooth, elegant animations
      const tl = gsap.timeline({
        defaults: { 
          ease: "power3.out",
          duration: 0.8
        }
      });

      // Animate stats cards with a smooth fade and scale
      tl.to(statsCardsRef.current, {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.7,
        ease: "power2.out",
      })
      // Then animate the main chart
      .to(chartRef.current, {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.7,
        ease: "power2.out",
      }, "-=0.5")
      // Animate row 3 elements with elegant stagger
      .to(row3Refs.current, {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.6,
        stagger: {
          amount: 0.3,
          from: "start"
        },
        ease: "power2.out",
      }, "-=0.4")
      // Animate row 4 elements with elegant stagger
      .to(row4Refs.current, {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.6,
        stagger: {
          amount: 0.3,
          from: "start"
        },
        ease: "power2.out",
      }, "-=0.4");

      // Optional: Add a subtle entrance for the entire container
      gsap.fromTo(containerRef.current,
        {
          opacity: 0.8,
        },
        {
          opacity: 1,
          duration: 1,
          ease: "power2.out"
        }
      );

    }, containerRef);

    return () => {
      ctx.revert();
    };
  }, [statistics]);

  // Helper function to add refs to arrays
  const addToRow3Refs = (el: HTMLDivElement | null) => {
    if (el && !row3Refs.current.includes(el)) {
      row3Refs.current.push(el);
    }
  };

  const addToRow4Refs = (el: HTMLDivElement | null) => {
    if (el && !row4Refs.current.includes(el)) {
      row4Refs.current.push(el);
    }
  };

  return (
    <div ref={containerRef} className="space-y-6">
      {/* Row 1: Key Stats Cards - Full Width */}
      <div ref={statsCardsRef} className="">
        <OverallStatsCards overallStats={statistics.overall} />
      </div>

      {/* Row 2: Main Chart - Full Width */}
      <div ref={chartRef}>
        <PerformanceTrendsChart
          trends={statistics.performance_trends_by_test_type}
        />
      </div>

      {/* Grid for subsequent multi-column rows */}
      <div ref={gridRef} className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Row 3: Detailed Breakdowns */}
        <div ref={addToRow3Refs} className="lg:col-span-7">
          <SectionPerformanceBreakdown
            performance={statistics.performance_by_section}
          />
        </div>
        <div ref={addToRow3Refs} className="lg:col-span-5">
          <ActionableInsightsTabs
            skills={statistics.skill_proficiency_summary}
            tests={statistics.test_history_summary}
          />
        </div>

        {/* Row 4: Summaries & Secondary Analytics */}
        <div ref={addToRow4Refs} className="lg:col-span-7">
          <AverageScoresByTypeCard
            scoresByType={statistics.average_scores_by_test_type}
          />
        </div>
        <div ref={addToRow4Refs} className="lg:col-span-5">
          <TimeAnalyticsCard timeAnalytics={statistics.time_analytics} />
        </div>
      </div>
    </div>
  );
}
