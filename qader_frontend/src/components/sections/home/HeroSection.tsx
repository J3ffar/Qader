import React from "react"; // Added React import
import Image from "next/image";
import { Button } from "@/components/ui/button"; // Assuming ui is directly under components

const HeroSection = () => {
  return (
    <div className="flex justify-center items-center flex-col gap-8 mt-11 w-full p-6">
      {/* Title */}
      <div className="flex justify-center items-center gap-4 text-center">
        {" "}
        {/* Added text-center for better mobile */}
        <Image
          src="/images/container.png"
          alt="Qader icon" // Add descriptive alt text
          width={60}
          height={60}
          className="max-w-full h-auto flex-shrink-0" // Added flex-shrink-0
        />
        <h1 className="text-5xl font-medium max-lg:text-4xl max-md:text-3xl">
          عندك <span className="text-[#e78b48]">اختبار قدرات؟</span> ومحتاج
          مساعدة!!
        </h1>
      </div>

      {/* Subtitle */}
      <p className="text-xl text-center max-w-xl mx-auto">
                       منصتنا مخصصة لك, انت فى الطريق الصحيح.منصتنا مخصصة لك, انت فى الطريق الصحيح منصتنا مخصصة لك, انت فى الطريق الصحيح.
</p>
      {/* Action Buttons */}
      <div className="gap-3 flex items-center">
        <Button variant="outline">
          <span> اشتراك</span>
        </Button>
        <Button variant="default">
          <span>تعرف علينا</span>
        </Button>
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
  );
};

export default HeroSection;
