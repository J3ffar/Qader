"use client";

import React, { useState } from "react";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";
import Image from "next/image";
import PartnersModal from "./PartnersModal"; // We'll keep the modal separate for clarity
import type { PartnersPageData } from "@/types/api/content.types";

// The props for this component will be the data fetched on the server
interface PartnersClientProps {
  data: PartnersPageData | null;
}

// This is the main client component that handles state
const PartnersClient: React.FC<PartnersClientProps> = ({ data }) => {
  const [showPopup, setShowPopup] = useState(false);

  // If data fetching failed on the server, show an error message
  if (!data) {
    return (
      <div className="flex flex-col justify-center items-center h-screen dark:bg-[#081028]">
        <h2 className="text-3xl font-bold">
          عذراً، لم نتمكن من تحميل محتوى الصفحة.
        </h2>
      </div>
    );
  }

  const partnerCategories = data.partner_categories ?? [];
  console.log(partnerCategories);
  const pageContent = data.page_content?.content_structured_resolved;

  // Extract all text and images from the single `page_content` object
  const heroTitle = pageContent?.hero_title?.value ?? "شركاء النجاح";
  const heroSubtitle =
    pageContent?.hero_subtitle?.value ?? "نؤمن بقوة التعاون لتحقيق أهداف أكبر.";
  const whyPartnerTitle =
    pageContent?.why_partner_title?.value ?? "لماذا الشراكة معنا؟";
  const whyPartnerText =
    pageContent?.why_partner_text?.value ??
    "نقدم تجربة فريدة لدعم طلابك وتحقيق أفضل النتائج.";
  const whyPartnerImage =
    pageContent?.why_partner_image?.value ?? "/images/logo.png";

  return (
    <div className="p-8 dark:bg-[#081028]">
      <div className="flex justify-center items-center flex-col container mx-auto text-center">
        <h2 className="text-4xl font-bold">{heroTitle}</h2>
        <p className="text-gray-800 text-lg max-w-xl mt-4 dark:text-[#D9E1FA]">
          {heroSubtitle}
        </p>
      </div>

      <div className="grid justify-center items-center gap-4 mt-10 md:grid-cols-3 sm:grid-cols-2 grid-cols-1 container mx-auto">
        {partnerCategories.map((partner, index) => {
          // --- START OF FIX ---
          // Provide a default local image based on the partner's index
          const defaultIcon = `/images/partner${index + 1}.png`;
          const iconSrc = partner.icon_image ?? defaultIcon;
          // --- END OF FIX ---

          return (
            <div
              key={partner.id}
              className="flex flex-col gap-4 justify-center items-center p-4 bg-[#f7fafe] rounded-3xl border border-[#cfe4fc] dark:border-gray-700 hover:border-[#56769b] dark:bg-[#0B1739] hover:scale-105 transition delay-150 duration-300 ease-in-out text-center"
            >
              <Image src={iconSrc} width={70} height={70} alt={partner.name} />
              <h3 className="text-2xl font-bold">{partner.name}</h3>
              <p>{partner.description}</p>
              <button
                onClick={() => setShowPopup(true)}
                className="w-full mt-auto flex justify-center gap-2 py-3 px-2 rounded-lg bg-[#074182] text-[#FDFDFD] font-semibold hover:bg-[#053061] transition-all"
              >
                قدم طلب شراكة <PaperAirplaneIcon className="w-5 h-5" />
              </button>
            </div>
          );
        })}
      </div>

      {/* "Why Partner" section */}
      <div className="flex justify-center items-center gap-14 mt-14 max-md:flex-col-reverse">
        <div className="flex-1">
          <h3 className="text-3xl font-bold text-[#074182] dark:text-[#FDFDFD]">
            {whyPartnerTitle}
          </h3>
          <p className="mt-4 text-lg leading-relaxed">{whyPartnerText}</p>
        </div>
        <div className="flex-1 flex justify-center">
          <Image
            src={whyPartnerImage}
            width={400}
            height={400}
            alt={whyPartnerTitle}
          />
        </div>
      </div>

      <PartnersModal
        partnerCategories={partnerCategories}
        show={showPopup}
        onClose={() => setShowPopup(false)}
      />
    </div>
  );
};

export default PartnersClient;
