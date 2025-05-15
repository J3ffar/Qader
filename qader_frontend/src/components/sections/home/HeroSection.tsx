"use client"
import React, { useState } from "react"; // Added React import
import Image from "next/image";
import { Button } from "@/components/ui/button"; // Assuming ui is directly under components
import LoginModal from "@/components/auth/LoginModal";
import SignupModal from "@/components/auth/SignupModal";

const HeroSection = ({data} : any) => {

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
    <div className=" bg-[#F9F9FA] dark:bg-[#0B1739] font-body">
    <div className="flex justify-center items-center flex-col gap-4 w-full p-6 pt-11 container mx-auto px-10">
      {/* Title */}
      <div className="flex justify-center items-center gap-6 text-center py-2 px-4 rounded-[16px] bg-[#FFF] dark:bg-[#D1DBF9] dark:text-black">
        {" "}
        {/* Added text-center for better mobile */}
        <Image
          src="/images/container.png"
          alt="Qader icon" // Add descriptive alt text
          width={60}
          height={60}
          className="max-w-full h-auto flex-shrink-0" // Added flex-shrink-0
        />
       
       <h1 className="lg:text-6xl md:text-5xl font-medium max-lg:text-4xl max-md:text-3xl">
  {data?.intro?.title ? (
    data.intro.title
  ) : (
    <>
      عندك{" "}
      <span className="text-[#e78b48]">
        اختبار قدرات؟
      </span>{" "}
      ومحتاج مساعدة!!
    </>
  )}
</h1>
      </div>

      {/* Subtitle */}
      <p className="md:text-xl sm:text-lg text-center max-w-[860px] mx-auto px-5 text-[#333333] dark:text-[#D9E1FA]">
                     {
                      data?.intro?.content ? data.intro.content : "منصتنا مخصصة لك, انت فى الطريق الصحيح.منصتنا مخصصة لك, انت فى الطريق الصحيح منصتنا مخصصة لك, انت فى الطريق الصحيح."
                     }  
</p>
      {/* Action Buttons */}
      <div className="gap-3 flex items-center mt-5 mb-7">
        <button className="   flex justify-center gap-2 min-[1120px]:py-3 sm:w-[180px] w-[100px]  p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer" onClick={openSignup}>
          <span> اشترك</span>
        </button>
        <a href="/about">
        <button  className=" flex justify-center gap-2 min-[1120px]:py-2.5  sm:w-[180px] w-[100px] p-2 rounded-[8px] bg-transparent border-[1.5px] border-[#074182]  text-[#074182] dark:border-[#3D93F5]  dark:text-[#3D93F5] font-[600] hover:bg-[#07418211] dark:hover:bg-[#3D93F511] transition-all cursor-pointer">
          <span>تعرف علينا</span>
        </button>
        </a>
      </div>

      {/* Main Hero Image */}
      <Image
        src="/images/photo.png"
        alt="Student studying for Qudorat test" // Add descriptive alt text
        width={800}
        height={800} // Adjust height based on aspect ratio if needed
        priority // Add priority as this is likely the LCP image
      />
    </div>

    <LoginModal
        show={showLogin}
        onClose={() => setShowLogin(false)}
        onSwitchToSignup={switchToSignup} // Pass switch handler
      />
      <SignupModal
        show={showSignup}
        onClose={() => setShowSignup(false)}
        onSwitchToLogin={switchToLogin} // Pass switch handler
      />
    </div>
  );
};

export default HeroSection;
