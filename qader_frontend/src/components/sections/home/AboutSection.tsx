import React from "react";
import Image from "next/image";
import { ArrowUpLeft } from "lucide-react";
import { Button } from "@/components/ui/button"; // Assuming ui is directly under components
import { div } from "framer-motion/client";

const AboutSection = () => {
  return (
    <div className=" bg-[#FDFDFD] dark:bg-[#081028]">
    <div className="flex justify-center items-center py-6 gap-7 max-md:flex-col-reverse h-full container mx-auto px-0 ">
      {/* Image Section */}
      <div>
        <Image
          src="/images/video.png" // Use absolute path from /public
          alt="Video presentation placeholder" // Add descriptive alt text
          width={600}
          height={600}
          priority // Consider adding priority if it's above the fold
        />
      </div>
      {/* Text Content Section */}
      <div>
        <h2 className="text-4xl font-bold">من نحن؟</h2>
        <p className="text-xl mt-4 text-gray-600 max-w-xl dark:text-[#D9E1FA]">
          هنا يمكنك تقديم نفسك و من انت و ما القصة التى تريد ان ترويها عن علامتك
          التجارية او عملك
        </p>
        <Button variant="outline" className="mt-4 py-5">
          <span>تعرف علينا اكثر</span>
          <ArrowUpLeft className="w-5 h-5 mr-2" />{" "}
          {/* Added margin for spacing */}
        </Button>
      </div>
    </div>
    </div>
  );
};

export default AboutSection;
