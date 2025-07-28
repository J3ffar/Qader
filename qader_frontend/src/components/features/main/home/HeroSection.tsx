"use client";
import React, { useState } from "react";
import Image from "next/image";
import LoginModal from "@/components/auth/LoginModal";
import SignupModal from "@/components/auth/SignupModal";
import type { HomepageData } from "@/types/api/content.types";

type HeroProps = {
  data: HomepageData["intro"];
};

const HeroSection = ({ data }: HeroProps) => {
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);

  const switchToLogin = () => {
    setShowSignup(false);
    setShowLogin(true);
  };

  const switchToSignup = () => {
    setShowLogin(false);
    setShowSignup(true);
  };

  const openSignup = () => {
    setShowSignup(true);
    setShowLogin(false);
  };

  const heroTitle =
    data?.content_structured_resolved.hero_title.value ??
    "عندك <span class='text-[#e78b48]'>اختبار قدرات؟</span> ومحتاج مساعدة!!";
  const subtitle =
    data?.content_structured_resolved?.hero_subtitle?.value ??
    "منصتنا مخصصة لك, انت فى الطريق الصحيح. اكتشف كيف يمكن لأدواتنا المبتكرة أن تضعك على طريق النجاح.";
  const promoIcon =
    data?.content_structured_resolved?.promo_icon?.value ??
    "/images/container.png";
  const heroImage =
    data?.content_structured_resolved?.main_hero_image?.value ??
    "/images/photo.png";

  return (
    <div className=" bg-[#F9F9FA] dark:bg-[#0B1739] font-body">
      <div className="flex justify-center items-center flex-col gap-4 w-full p-6 pt-11 container mx-auto px-10">
        {/* Title */}
        <div className="flex justify-center items-center gap-6 text-center py-2 px-4 rounded-[16px] bg-[#FFF] dark:bg-[#D1DBF9] dark:text-black">
          <Image
            src={promoIcon}
            alt="أيقونة قادر"
            width={60}
            height={60}
            className="max-w-full h-auto flex-shrink-0"
          />
          <h1
            className="lg:text-6xl md:text-5xl font-medium max-lg:text-4xl max-md:text-3xl"
            dangerouslySetInnerHTML={{ __html: heroTitle }}
          />
        </div>

        {/* Subtitle */}
        <p className="md:text-xl sm:text-lg text-center max-w-[860px] mx-auto px-5 text-[#333333] dark:text-[#D9E1FA]">
          {subtitle}
        </p>

        {/* Action Buttons */}
        <div className="gap-3 flex items-center mt-5 mb-7">
          <button
            className="flex justify-center gap-2 min-[1120px]:py-3 sm:w-[180px] w-[100px] p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer"
            onClick={openSignup}
          >
            <span>اشترك</span>
          </button>
          <a href="/about">
            <button className="flex justify-center gap-2 min-[1120px]:py-2.5 sm:w-[180px] w-[100px] p-2 rounded-[8px] bg-transparent border-[1.5px] border-[#074182] text-[#074182] dark:border-[#3D93F5] dark:text-[#3D93F5] font-[600] hover:bg-[#07418211] dark:hover:bg-[#3D93F511] transition-all cursor-pointer">
              <span>تعرف علينا</span>
            </button>
          </a>
        </div>

        {/* Main Hero Image */}
        <Image
          src={heroImage}
          alt="طالب يدرس لاختبار القدرات"
          width={800}
          height={800}
          priority
        />
      </div>

      <LoginModal
        show={showLogin}
        onClose={() => setShowLogin(false)}
        onSwitchToSignup={switchToSignup}
      />
      <SignupModal
        show={showSignup}
        onClose={() => setShowSignup(false)}
        onSwitchToLogin={switchToLogin}
      />
    </div>
  );
};

export default HeroSection;
