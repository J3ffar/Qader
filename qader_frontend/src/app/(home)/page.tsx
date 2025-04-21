import HeroSection from "@/components/sections/home/HeroSection";
import AboutSection from "@/components/sections/home/AboutSection";
import ReviewSection from "@/components/sections/home/ReviewSection";
import AdvantageSection from "@/components/sections/home/AdvantageSection";
import StatisticsSection from "@/components/sections/home/StatisticsSection";
import CallToActionSection from "@/components/sections/home/CallToActionSection";

export default function Home() {
  return (
    <div className="container mx-auto px-4">
      <HeroSection />
      <AboutSection />
      <ReviewSection />
      <AdvantageSection />
      <StatisticsSection />
      <CallToActionSection />
    </div>
  );
}
