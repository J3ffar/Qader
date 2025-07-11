import React from "react";
import { User } from "lucide-react";
import type { HomepageData, Review } from "@/types/api/content.types";

type ReviewProps = {
  data: HomepageData["praise"];
};

const ReviewCard = ({ review }: { review: Review }) => (
  <div
    className={`w-full shadow-xl rounded-2xl flex flex-col justify-start items-center text-center border-r-8 p-6 sm:p-8 border-r-[#e78b48] transition-all delay-150 duration-300 ease-in-out hover:bg-[#E7F1FE4D] dark:hover:bg-[#053061] hover:border-r-[#074182] hover:shadow-2xl hover:scale-105 bg-card text-card-foreground`}
  >
    <div className="w-14 h-14 mb-4 flex justify-center items-center rounded-full bg-[#EDEDED]">
      <User className="w-6 h-6 text-muted-foreground" />
    </div>
    <h3 className="font-bold text-lg">{review.name}</h3>
    <p className="text-sm text-muted-foreground mb-3">{review.title}</p>
    <p className="text-base">"{review.quote}"</p>
  </div>
);

const ReviewSection = ({ data }: ReviewProps) => {
  const title =
    data?.content_structured_resolved?.section_title?.value ??
    "ماذا قالوا <span class='text-[#074182] dark:text-[#3D93F5]'>عنا؟</span>";
  const subtitle =
    data?.content_structured_resolved?.section_subtitle?.value ??
    "آراء طلابنا هي شهادة نجاحنا.";
  const reviews = data?.content_structured_resolved?.reviews?.value ?? [];

  return (
    <div className=" bg-[#F9F9FA] dark:bg-[#0B1739] sm:px-0 px-4">
      <div className="py-6 sm:py-8 md:py-10 container mx-auto px-0">
        <div className="mb-8 text-center sm:text-right">
          <h2
            className="text-4xl font-bold mb-2"
            dangerouslySetInnerHTML={{ __html: title }}
          />
          <p className="text-lg text-muted-foreground dark:text-[#D9E1FA]">
            {subtitle}
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {reviews.map((review, index) => (
            <ReviewCard key={index} review={review} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ReviewSection;
