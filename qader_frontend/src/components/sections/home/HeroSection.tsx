import React from "react"; // Added React import
import Image from "next/image";
import { Button } from "@/components/ui/button"; // Assuming ui is directly under components

const HeroSection = () => {
  return (
    <div className=" bg-[#F9F9FA] dark:bg-[#0B1739] font-body">
    <div className="flex justify-center items-center flex-col gap-8 w-full p-6 pt-11 container mx-auto px-10">
      {/* Title */}
      <div className="flex justify-center items-center gap-4 text-center p-2 rounded-[16px] bg-[#FFF] dark:bg-[#D1DBF9] dark:text-black">
        {" "}
        {/* Added text-center for better mobile */}
        <Image
          src="/images/container.png"
          alt="Qader icon" // Add descriptive alt text
          width={60}
          height={60}
          className="max-w-full h-auto flex-shrink-0" // Added flex-shrink-0
        />
       
        <h1 className="lg:text-6xl md:text-5xl font-medium max-lg:text-4xl max-md:text-3xl ">
          عندك <span className="text-[#e78b48] ">اختبار قدرات؟</span> ومحتاج
          مساعدة!!
        </h1>
      </div>

      {/* Subtitle */}
      <p className="text-xl text-center max-w-xl mx-auto">
                       منصتنا مخصصة لك, انت فى الطريق الصحيح.منصتنا مخصصة لك, انت فى الطريق الصحيح منصتنا مخصصة لك, انت فى الطريق الصحيح.
</p>
      {/* Action Buttons */}
      <div className="gap-3 flex items-center">
        <Button variant="outline" className=" border-[2px] hover:border-[2px] font-[700] hover:border-[#074182] dark:hover:border-[#3D93F5] dark:border-[#3D93F5] dark:bg-[#3D93F5] hover:dark:bg-transparent ">
          <span> اشتراك</span>
        </Button>
        <Button variant="default" className="  border-[2px] font-[700] hover:border-[#074182] dark:hover:border-[#3D93F5] dark:border-[#3D93F5] bg-transparent">
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
    </div>
  );
};

export default HeroSection;
