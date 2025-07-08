"use client";
import React, { useState } from "react";
import LoginModal from "@/components/auth/LoginModal";
import SignupModal from "@/components/auth/SignupModal";
import type { HomepageData } from "@/types/api/content.types";

type CTAProps = {
  data: HomepageData["call_to_action"];
};

const CallToActionSection = ({ data }: CTAProps) => {
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

  const title =
    data?.content_structured_resolved?.title?.value ??
    "هل أنت مستعد للنجاح في اختبار القدرات؟";
  const subtitle =
    data?.content_structured_resolved?.subtitle?.value ??
    "انضم لآلاف الطلاب الذين حققوا أهدافهم مع منصة قادر. ابدأ رحلتك الآن!";
  const buttonText =
    data?.content_structured_resolved?.button_text?.value ?? "اشتراك";

  return (
    <div className=" bg-[#FDFDFD] dark:bg-[#0B1739] sm:px-0 px-4">
      <div className="flex justify-center items-center flex-col py-9 container mx-auto px-0 gap-4 text-center ">
        <h2 className="text-4xl font-bold">{title}</h2>
        <p className="text-xl max-w-xl">{subtitle}</p>
        <button
          onClick={openSignup}
          className=" mt-4 flex justify-center gap-2 min-[1120px]:py-3 sm:w-[280px] w-[180px] p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer"
        >
          <span>{buttonText}</span>
        </button>
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

export default CallToActionSection;
