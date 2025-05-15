import React from "react";
import { User } from "lucide-react";

// Define review data outside the component
const reviewsData = [
  {
    id: 1,
    name: "أحمد عبدالله", // Example Name
    title: "طالب", // Example Title
    quote:
      "منصة قادر ساعدتني كثيراً في التحضير لاختبار القدرات، شرح واضح وتمارين مفيدة.", // Example Quote
      borderColor: "border-r-[#e78b48]",
      initialScale: "",
      hoverBorder: "hover:border-r-[#074182]",
      hoverShadow: "hover:shadow-2xl",
      hoverScale: "hover:scale-105",
  },
  {
    id: 2,
    name: "فاطمة الزهراء",
    title: "طالبة",
    quote: "التنوع في الأسئلة والاختبارات التجريبية كان ممتازاً.",
    borderColor: "border-r-[#e78b48]",
    initialScale: "",
    hoverBorder: "hover:border-r-[#074182]",
    hoverShadow: "hover:shadow-2xl",
    hoverScale: "hover:scale-105",
  },
  {
    id: 3,
    name: "محمد علي",
    title: "طالب",
    quote: "أعجبني تصميم الموقع وسهولة الاستخدام.",
    borderColor: "border-r-[#e78b48]",
    initialScale: "",
    hoverBorder: "hover:border-r-[#074182]",
    hoverShadow: "hover:shadow-2xl",
    hoverScale: "hover:scale-105",
  },
];

const ReviewCard = ({ review  }: { review: (typeof reviewsData)[0] }) => (
  <div
    className={`w-full shadow-xl rounded-2xl flex flex-col justify-start items-center text-center border-r-8 p-6 sm:p-8 ${review.borderColor} transition-all delay-150 duration-300 ease-in-out hover:bg-[#E7F1FE4D] dark:hover:bg-[#053061] ${review.initialScale} ${review.hoverBorder} ${review.hoverShadow} ${review.hoverScale} bg-card text-card-foreground`} // Use theme colors, adjusted padding
  >
    <div className="w-14 h-14 mb-4 flex justify-center items-center rounded-full bg-[#EDEDED]">
      {" "}
      {/* Use muted color */}
      <User className="w-6 h-6 text-muted-foreground" />{" "}
      {/* Use muted foreground */}
    </div>
    <h3 className="font-bold text-lg">{review.name}</h3>
    <p className="text-sm text-muted-foreground mb-3">{review.title}</p>
    <p className="text-base">"{review.quote}"</p> {/* Added quotes */}
  </div>
);

const ReviewSection = () => {
  return (
    <div className=" bg-[#F9F9FA] dark:bg-[#0B1739] sm:px-0 px-4">
    <div className="py-6 sm:py-8 md:py-10 container mx-auto px-0">
      {" "}
      {/* Adjusted padding */}
      {/* Section Header */}
      <div className="mb-8 text-center sm:text-right">
        {" "}
        {/* Adjusted margin and alignment */}
        <h2 className="text-4xl font-bold mb-2">
          {" "}
          {/* Added margin */}
          ماذا قالوا <span className="text-[#074182] dark:text-[#3D93F5]">عنا؟</span>
        </h2>
        <p className="text-lg text-muted-foreground dark:text-[#D9E1FA]">
          {" "}
          {/* Use muted foreground, adjusted size */}
          ذكر شرح مختصر لعنوان المدح. {/* Example text */}
        </p>
      </div>
      {/* Reviews Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
        {" "}
        {/* Use grid for responsiveness */}
        {reviewsData.map((review) => (
          <ReviewCard key={review.id} review={review} />
        ))}
      </div>
    </div>
    </div>
  );
};

export default ReviewSection;
