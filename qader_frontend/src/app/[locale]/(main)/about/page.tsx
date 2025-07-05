import React from "react";
import Image from "next/image";
// Using static icons as per the immediate fix
import {
  UsersIcon,
  BookOpenIcon,
  SparklesIcon,
} from "@heroicons/react/24/solid";
import { getAboutPageContent } from "@/services/content.service";

// This component remains the same from the last fix (using static icons)
const StoryCardIcon = ({ index }: { index: number }) => {
  const iconClass = "w-8 h-8 text-[#172bab]";
  switch (index) {
    case 0:
      return <BookOpenIcon className={iconClass} />;
    case 1:
      return <UsersIcon className={iconClass} />;
    case 2:
      return <SparklesIcon className={iconClass} />;
    default:
      return null;
  }
};

const AboutPage = async () => {
  const data = await getAboutPageContent();

  if (!data) {
    return (
      <div className="flex flex-col justify-center items-center h-screen dark:bg-[#081028]">
        <h2 className="text-3xl font-bold">
          عذراً، لم نتمكن من تحميل محتوى الصفحة.
        </h2>
        <p className="text-lg mt-4">يرجى المحاولة مرة أخرى لاحقاً.</p>
      </div>
    );
  }

  const content = data.content_structured_resolved;
  console.log(content);
  // --- START OF THE FIX ---
  // Define variables for image URLs with fallbacks to local defaults.
  // The nullish coalescing operator (??) is perfect for this.
  const mainPromoImage = content.main_promo_image?.value ?? "/images/phon.png";
  const whyDifferentImage =
    content.why_different_image?.value ?? "/images/labtop.png";
  const missionImage = content.mission_image?.value ?? "/images/labtop1.png";
  // --- END OF THE FIX ---

  return (
    <div className="flex flex-col justify-center items-center gap-7 p-7 dark:bg-[#081028] sm:px-0 px-4">
      <h2
        className="text-5xl font-bold text-center"
        dangerouslySetInnerHTML={{ __html: content.hero_title.value }}
      />
      <p
        className="text-lg max-w-xl text-center"
        dangerouslySetInnerHTML={{ __html: content.hero_subtitle.value }}
      />

      {/* Story Cards Section */}
      <div className="flex justify-center gap-6 p-9 max-md:flex-col ">
        {content.story_cards.value.map((card, index) => (
          <div
            key={index}
            className="bg-[#e7f1fe] rounded-3xl flex flex-1 flex-col gap-5 justify-center items-center p-4 border border-[#cfe4fc] dark:bg-[#0B1739]"
          >
            <span className="w-16 h-16 rounded-full flex justify-center items-center bg-[#e7f1fe] shadow-2xl inset-shadow-sm border border-[#9ec9fa]">
              <StoryCardIcon index={index} />
            </span>
            <p
              className="text-center text-lg"
              dangerouslySetInnerHTML={{ __html: card.text }}
            />
          </div>
        ))}
      </div>

      {/* Main Promo Image with fallback */}
      <Image
        src={mainPromoImage}
        width={700}
        height={700}
        alt="عرض تطبيق قادر"
      />

      {/* Details Section */}
      <div className="bg-[#E7F1FE4D] rounded-2xl mx-11 my-9 p-7 dark:bg-[#0B1739]">
        {/* Why Different Section with fallback */}
        <div className="flex justify-between items-center gap-20 max-lg:gap-7 max-lg:flex-col-reverse">
          <div>
            <h3 className="text-3xl font-bold">
              {content.why_different_title.value}
            </h3>
            <ul className="list-disc list-inside text-right text-lg space-y-2 mt-2">
              {content.why_different_points.value.map((item, index) => (
                <li key={index}>{item.point}</li>
              ))}
            </ul>
          </div>
          <Image
            src={whyDifferentImage}
            width={500}
            height={500}
            alt="لماذا نحن مختلفون"
          />
        </div>

        {/* Mission Section with fallback */}
        <div className="flex justify-between items-center gap-20 max-lg:gap-7 max-lg:flex-col mt-9">
          <Image src={missionImage} width={500} height={500} alt="رسالتنا" />
          <div>
            <h3 className="text-3xl font-bold">
              {content.mission_title.value}
            </h3>
            <div
              className="list-disc list-inside text-right text-lg mt-2"
              dangerouslySetInnerHTML={{
                __html: `<li>${content.mission_text.value}</li>`,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;
