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

const AdvantageSection = () => {
  return (
    <div className="h-full flex justify-center items-center max-md:flex-col-reverse p-6 gap-9">
      {/* Text Content Section */}
      <div className="w-full flex-1/2">
        {" "}
        {/* Consider using flex-grow or specific widths */}
        <h3 className="text-4xl font-bold">
          لماذا يجب على العملاء أن يختارونا؟
        </h3>
        <p className="text-xl text-gray-600">
          ما الذى يجعلنا نتميز عن المنافسين.
        </p>
        <div className="flex flex-col gap-3 mt-6">
          {advantages.map((advantage) => (
            <p
              key={advantage.id}
              className={`p-4 rounded-3xl transition delay-150 duration-300 ease-in-out ${
                advantage.initialBg
              } ${advantage.initialText} ${
                advantage.id !== 1 ? "hover:bg-[#074182] hover:text-white" : "" // Apply hover only if not the first item
              }`}
            >
              {`${advantage.id} ${advantage.text}`} {/* Use template literal */}
            </p>
          ))}
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
  );
};

export default AdvantageSection;
