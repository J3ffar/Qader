"use client"
import React, { useState } from "react";
import { Button } from "@/components/ui/button"; // Assuming ui is directly under components
import LoginModal from "@/components/auth/LoginModal";
import SignupModal from "@/components/auth/SignupModal";

const CallToActionSection = () => {
   const [showLogin, setShowLogin] = useState(false);
      const [showSignup, setShowSignup] = useState(false);
  
  
    const switchToLogin = () => {
      setShowSignup(false);
      setShowLogin(true);
    };
  
    // Function to switch from login to signup
    const switchToSignup = () => {
      setShowLogin(false);
      setShowSignup(true);
    };
  
    const openSignup = () => {
      setShowSignup(true);
      setShowLogin(false); // Close login if open
    };
  return (
    <div className=" bg-[#FDFDFD] dark:bg-[#0B1739] sm:px-0 px-4">
    <div className="flex justify-center items-center flex-col py-9 container mx-auto px-0 gap-4 text-center ">
      {" "}
      {/* Added background, margin, rounding, shadow */}
      <h2 className="text-4xl font-bold">
        هل أنت مستعد للنجاح في اختبار القدرات؟ {/* More engaging text */}
      </h2>
      <p className="text-xl max-w-xl">
        {" "}
        {/* Added max-width */}
        انضم لآلاف الطلاب الذين حققوا أهدافهم مع منصة قادر. ابدأ رحلتك الآن!{" "}
        {/* More engaging text */}
      </p>
      {/* Link this button appropriately */}
      <button onClick={openSignup}
className=" mt-4  flex justify-center gap-2 min-[1120px]:py-3 sm:w-[280px] w-[180px]
p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD]  hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer"      >
        {" "}
        {/* Styled outline button */}
        <span>  اشتراك</span> {/* Clearer CTA */}
      </button>
    </div>

    <LoginModal
        show={showLogin}
        onClose={() => setShowLogin(false)}
        onSwitchToSignup={switchToSignup}
         // Pass switch handler
      />
      <SignupModal
        show={showSignup}
        onClose={() => setShowSignup(false)}
        onSwitchToLogin={switchToLogin} // Pass switch handler
      />
    </div>
  );
};

export default CallToActionSection;
