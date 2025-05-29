"use client";

import { useEffect, useState } from "react";
import HeroSection from "@/components/sections/home/HeroSection";
import AboutSection from "@/components/sections/home/AboutSection";
import ReviewSection from "@/components/sections/home/ReviewSection";
import AdvantageSection from "@/components/sections/home/AdvantageSection";
import StatisticsSection from "@/components/sections/home/StatisticsSection";
import CallToActionSection from "@/components/sections/home/CallToActionSection";

export default function Home() {
  const [myData, setMyData] = useState<any>();
  useEffect(() => {
    const fetchHomepageContent = async () => {
      try {
        const res = await fetch(
          "https://qader.vip/ar/api/v1/content/homepage/"
        );
        const data: any = await res.json();
        setMyData(data);
        console.log("📦 Homepage API Response:", data);
      } catch (error) {
        console.error("❌ Failed to fetch homepage data:", error);
      }
    };

    fetchHomepageContent();
  }, []);

  return (
    <div>
      <HeroSection data={myData} />
      <AboutSection data={myData} />
      <ReviewSection />
      <AdvantageSection data={myData} />
      <StatisticsSection data={myData} />
      <CallToActionSection />
    </div>
  );
}
