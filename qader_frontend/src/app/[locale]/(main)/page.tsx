import HeroSection from "@/components/features/main/home/HeroSection";
import AboutSection from "@/components/features/main/home/AboutSection";
import ReviewSection from "@/components/features/main/home/ReviewSection";
import AdvantageSection from "@/components/features/main/home/AdvantageSection";
import StatisticsSection from "@/components/features/main/home/StatisticsSection";
import CallToActionSection from "@/components/features/main/home/CallToActionSection";
import { getHomepageContent } from "@/services/content.service";

export default async function Home() {
  const data = await getHomepageContent();

  if (!data) {
    return (
      <p className="text-center py-20">لا يمكن تحميل محتوى الصفحة حالياً.</p>
    );
  }

  return (
    <div>
      {data.intro && <HeroSection data={data.intro} />}

      {data.about_us && <AboutSection data={data.about_us} />}

      {data.praise && <ReviewSection data={data.praise} />}

      {data.why_partner_text && data.features && data.features.length > 0 && (
        <AdvantageSection
          data={{
            features: data.features,
            partnerText: data.why_partner_text,
          }}
        />
      )}

      {data.statistics && data.statistics.length > 0 && (
        <StatisticsSection data={data.statistics} />
      )}

      {data.call_to_action && (
        <CallToActionSection data={data.call_to_action} />
      )}
    </div>
  );
}
