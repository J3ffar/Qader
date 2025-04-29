import React from "react";
import { Button } from "@/components/ui/button"; // Assuming ui is directly under components

const CallToActionSection = () => {
  return (
    <div className="flex justify-center items-center flex-col p-8 gap-4 text-center my-8">
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
        className="px-8 py-3 text-lg"
      >
        {" "}
        {/* Styled outline button */}
        <span> ابدأ الآن / اشتراك</span> {/* Clearer CTA */}
      </Button>
    </div>
  );
};

export default CallToActionSection;
