import React from "react";
import type { Statistic } from "@/types/api/content.types";

type StatisticsProps = {
  data: Statistic[];
};

const StatisticsSection = ({ data }: StatisticsProps) => {
  return (
    <div className=" bg-white dark:bg-[#081028] sm:px-0 px-4">
      <div className="flex flex-col justify-center items-center py-9 container mx-auto px-0">
        <h2 className="text-4xl font-bold mb-2 text-center">
          تعرف على إحصائياتنا
        </h2>
        <p className="text-xl mb-8 text-center dark:text-[#D9E1FA]">
          أرقامنا تتحدث عن نجاحنا وثقة طلابنا.
        </p>
        <div className="flex justify-center items-center flex-wrap gap-4 w-full">
          {data.map((stat, index) => (
            <div
              key={index}
              className="py-5 px-2 rounded-lg text-2xl font-bold flex justify-center items-center flex-col border-2 bg-[#E7F1FE4D] border-[#cfe4fc] dark:bg-[#0B1739] dark:hover:bg-[#053061] shadow-md w-full max-w-[330px] grow"
            >
              <h3 className="text-primary lg:text-4xl md:text-3xl text-2xl mb-1">
                {stat.value}
              </h3>
              <h3 className="text-foreground lg:text-3xl md:text-2xl text-xl">
                {stat.label}
              </h3>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StatisticsSection;
