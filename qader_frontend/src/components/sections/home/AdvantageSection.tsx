import React from "react";
import Image from "next/image";

// Define advantage data outside the component
const advantages = [
  {
    id: 1,
    text: "الميزة الرئيسية 1",
    initialBg: "bg-[#074182]",
    initialText: "text-white",
  },
  {
    id: 2,
    text: "الميزة الرئيسية 2",
    initialBg: "bg-[#e7f1fe]",
    initialText: "text-black",
  }, // Assuming default text is black/gray
  {
    id: 3,
    text: "الميزة الرئيسية 3",
    initialBg: "bg-[#e7f1fe]",
    initialText: "text-black",
  },
  {
    id: 4,
    text: "الميزة الرئيسية 4",
    initialBg: "bg-[#e7f1fe]",
    initialText: "text-black",
  },
];

const AdvantageSection = ({data} : any) => {
  return (
    <div className=" bg-white dark:bg-[#081028] sm:px-0 px-4">
    <div className="h-full flex justify-center items-center max-md:flex-col-reverse py-6 container mx-auto px-0 gap-9">
      {/* Text Content Section */}
      <div className="w-full flex-1/2">
        {" "}
        {/* Consider using flex-grow or specific widths */}
        <h3 className="text-4xl font-bold">
          لماذا يجب على العملاء أن يختارونا؟
        </h3>
        <p className="text-xl text-gray-600 dark:text-[#D9E1FA]">
          ما الذى يجعلنا نتميز عن المنافسين.
        </p>
        <div className="flex flex-col gap-3 mt-6">
  {data?.features && data.features.length > 0 ? (
    data.features.map((feature : any, index : any) => (
      <p
        key={index}
        className={`py-2 px-4 rounded-[16px] transition delay-150 duration-300 ease-in-out font-heading dark:bg-[#0B1739] bg-[#E7F1FE] hover:dark:bg-[#053061]
          hover:bg-[#074182] hover:text-[#FDFDFD] hover:dark:font-[600] hover:dark:text-[#FDFDFD] text-[22px]
        `}
      >
        {feature.title} - {feature.text}
      </p>
    ))
  ) : (
    advantages.map((advantage) => (
      <p
        key={advantage.id}
        className={`py-2 px-4 rounded-[16px] transition delay-150 duration-300 ease-in-out font-heading dark:bg-[#0B1739] bg-[#E7F1FE] hover:dark:bg-[#053061]
          hover:bg-[#074182] hover:text-[#FDFDFD] hover:dark:font-[600] hover:dark:text-[#FDFDFD] text-[22px]
        `}
      >
        {`${advantage.id}  ${advantage.text}`}
      </p>
    ))
  )}
</div>

      </div>
      {/* Image Section */}
      <div className="flex flex-1/2">
        {" "}
        {/* Consider using flex-grow or specific widths */}
        <Image
          src="/images/photo-1.png"
          alt="Illustration showing advantages" // Add descriptive alt text
          width={600}
          height={600}
        />
      </div>
    </div>
    </div>
  );
};

export default AdvantageSection;
