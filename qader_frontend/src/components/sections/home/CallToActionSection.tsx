import React from "react";
import { Button } from "@/components/ui/button"; // Assuming ui is directly under components

const CallToActionSection = () => {
  return (
    <div className=" bg-[#FDFDFD] dark:bg-[#081028]">
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
      <Button
        variant="outline"
        className="px-8 py-3 text-lg hover:border-[#074182] dark:hover:border-[#3D93F5] dark:border-[#3D93F5] dark:bg-[#3D93F5] hover:dark:bg-transparent"
      >
        {" "}
        {/* Styled outline button */}
        <span> ابدأ الآن / اشتراك</span> {/* Clearer CTA */}
      </Button>
    </div>
    </div>
  );
};

export default CallToActionSection;
