import React from "react";

// Define statistics data outside the component
const statsData = [
  { id: 1, value: "+5000", label: "اختبار مكتمل" }, // More specific label
  { id: 2, value: "+10000", label: "سؤال تدريبي" },
  { id: 3, value: "+2000", label: "طالب مسجل" },
];

const StatisticsSection = ({data} : any) => {
  return (
    <div className=" bg-white dark:bg-[#081028] sm:px-0 px-4">
    <div className="flex flex-col justify-center items-center py-9 container mx-auto px-0">
      {" "}
      {/* Added background, margin, rounding */}
      {/* Section Header */}
      <h2 className="text-4xl font-bold mb-2 text-center">
        تعرف على إحصائياتنا
      </h2>{" "}
      {/* Use إ not أ */}
      <p className="text-xl mb-8 text-center dark:text-[#D9E1FA]">
        {" "}
        {/* Use muted foreground, added margin */}
        قم بتضمين نص محمس عن الاحصائيات هنا.
      </p>
      {/* Statistics Cards */}
      <div className="flex justify-between items-center flex-wrap w-full">
  {data?.statistics && data.statistics.length > 0 ? (
    data.statistics.map((stat : any, index : any) => (
      <div
        key={index}
        className="py-5 px-2 rounded-lg text-2xl font-bold flex justify-center items-center flex-col border-2 bg-[#E7F1FE4D] border-[#cfe4fc] dark:bg-[#0B1739] dark:hover:bg-[#053061] shadow-md w-[330px] min-w-[250px] gradd"
      >
        <h3 className="text-primary lg:text-4xl md:text-3xl text-2xl mb-1">
          {stat.value}
        </h3>
        <h3 className="text-foreground lg:text-3xl md:text-2xl text-xl">
          {stat.label}
        </h3>
      </div>
    ))
  ) : (
    statsData.map((stat) => (
      <div
        key={stat.id}
        className="py-5 px-2 rounded-lg text-2xl font-bold flex justify-center items-center flex-col border-2 bg-[#E7F1FE4D] border-[#cfe4fc] dark:bg-[#0B1739] dark:hover:bg-[#053061] shadow-md w-[330px] min-w-[250px] gradd"
      >
        <h3 className="text-primary lg:text-4xl md:text-3xl text-2xl mb-1">
          {stat.value}
        </h3>
        <h3 className="text-foreground lg:text-3xl md:text-2xl text-xl">
          {stat.label}
        </h3>
      </div>
    ))
  )}
</div>
    </div>
    </div>
  );
};

export default StatisticsSection;
