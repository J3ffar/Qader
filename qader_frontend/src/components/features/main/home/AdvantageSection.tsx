import React from "react";
import Image from "next/image";
import type { HomepageData, Feature } from "@/types/api/content.types";

type AdvantageProps = {
  data: {
    features: Feature[];
    partnerText: HomepageData["why_partner_text"];
  };
};

const AdvantageSection = ({ data }: AdvantageProps) => {
  const title =
    data.partnerText?.content_structured_resolved.section_title.value ??
    "لماذا يجب على العملاء أن يختارونا؟";
  const subtitle =
    data.partnerText?.content_structured_resolved?.section_subtitle?.value ??
    "ما الذي يجعلنا نتميز عن المنافسين.";
  const mainImage =
    data.partnerText?.content_structured_resolved?.main_image?.value ??
    "/images/photo-1.png";

  return (
    <div className=" bg-white dark:bg-[#081028] sm:px-0 px-4">
      <div className="h-full flex justify-center items-center max-md:flex-col-reverse py-6 container mx-auto px-0 gap-9">
        {/* Text Content Section */}
        <div className="w-full flex-1">
          <h3 className="text-4xl font-bold">{title}</h3>
          <p className="text-xl text-gray-600 dark:text-[#D9E1FA]">
            {subtitle}
          </p>
          <div className="flex flex-col gap-3 mt-6">
            {data.features.map((feature, index) => (
              <div
                key={index}
                className={`py-2 px-4 rounded-[16px] transition delay-150 duration-300 ease-in-out dark:bg-[#0B1739] bg-[#E7F1FE] hover:dark:bg-[#053061] hover:bg-[#074182] hover:text-[#FDFDFD] hover:dark:font-[600] hover:dark:text-[#FDFDFD] `}
              >
                <h2 className="text-2xl font-heading">
                  {index + 1 + "."} {feature.title}
                </h2>
                <p className="text-md">{feature.text}</p>
              </div>
            ))}
          </div>
        </div>
        {/* Image Section */}
        <div className="flex flex-1 justify-center">
          <Image
            src={mainImage}
            alt="صورة توضيحية للمميزات"
            width={700}
            height={700}
          />
        </div>
      </div>
    </div>
  );
};

export default AdvantageSection;
