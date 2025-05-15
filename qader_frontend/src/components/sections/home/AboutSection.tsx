import React from "react";
import Image from "next/image";
import { ArrowUpLeft } from "lucide-react";
import { Button } from "@/components/ui/button"; // Assuming ui is directly under components
import { div } from "framer-motion/client";

const AboutSection = ({data} : any) => {
  return (
    <div className=" bg-white dark:bg-[#081028] sm:px-0 px-3">
    <div className="flex justify-center items-center py-6 gap-7 max-md:flex-col-reverse h-full container mx-auto px-0 ">
      {/* Image Section */}
      <div className="w-full max-w-[500px] h-auto">
  {data?.intro_video_url ? (
    <video
      src={data.intro_video_url}
      controls
      className="w-full h-auto rounded-lg object-cover"
    />
  ) : (
    <Image
      src="/images/video.png"
      alt="Video presentation placeholder"
      width={600}
      height={600}
      priority
      className="w-full h-auto rounded-lg object-cover"
    />
  )}
</div>

      {/* Text Content Section */}
      <div>
        <h2 className="text-4xl font-bold">من نحن؟</h2>
        <p className="text-xl mt-4 text-gray-600 max-w-xl dark:text-[#D9E1FA]">
          هنا يمكنك تقديم نفسك و من انت و ما القصة التى تريد ان ترويها عن علامتك
          التجارية او عملك
        </p>
        <a href="/about">
        <button  className=" mt-4  flex justify-center gap-2 min-[1120px]:py-3 w-[180px]
          p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD]  hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer">
          <span>تعرف علينا اكثر</span>
          <ArrowUpLeft className="w-5 h-5 mr-2" />{" "}
          {/* Added margin for spacing */}
        </button>
        </a>
      </div>
    </div>
    </div>
  );
};

export default AboutSection;
