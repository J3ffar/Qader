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
    borderColor: "border-r-[#074182]",
    initialScale: "scale-105",
    hoverBorder: "", // No hover change for the first one if intended
    hoverShadow: "", // No hover change for the first one if intended
    hoverScale: "", // No hover change for the first one if intended
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

const ReviewCard = ({ review }: { review: (typeof reviewsData)[0] }) => (
  <div
    className={`w-full shadow-xl rounded-2xl flex flex-col justify-start items-center text-center border-r-8 p-6 sm:p-8 ${review.borderColor} transition-all delay-150 duration-300 ease-in-out ${review.initialScale} ${review.hoverBorder} ${review.hoverShadow} ${review.hoverScale} bg-card text-card-foreground`} // Use theme colors, adjusted padding
  >
    <div className="w-14 h-14 mb-4 bg-muted flex justify-center items-center rounded-full">
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
    <div className="p-6 sm:p-8 md:p-10">
      {" "}
      {/* Adjusted padding */}
      {/* Section Header */}
      <div className="mb-8 text-center sm:text-right">
        {" "}
        {/* Adjusted margin and alignment */}
        <h2 className="text-4xl font-bold mb-2">
          {" "}
          {/* Added margin */}
          ماذا قالوا <span className="text-[#074182]">عنا؟</span>
        </h2>
        <p className="text-lg text-muted-foreground">
          {" "}
          {/* Use muted foreground, adjusted size */}
          آراء طلابنا وتجاربهم مع منصة قادر. {/* Example text */}
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
  );
};

export default ReviewSection;
