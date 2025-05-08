import React from "react";

// Define statistics data outside the component
const statsData = [
  { id: 1, value: "+5000", label: "اختبار مكتمل" }, // More specific label
  { id: 2, value: "+10000", label: "سؤال تدريبي" },
  { id: 3, value: "+2000", label: "طالب مسجل" },
];

const StatisticsSection = () => {
  return (
    <div className=" bg-[#F9F9FA] dark:bg-[#0B1739]">
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
        أرقام نفخر بها وتعكس نجاحنا مع طلابنا. {/* Example text */}
      </p>
      {/* Statistics Cards */}
      <div className="flex justify-between items-center  flex-wrap w-full">
        {statsData.map((stat) => (
          <div
            key={stat.id}
            className="py-5 px-2 bg-card rounded-lg text-2xl font-bold flex justify-center items-center flex-col border-2 border-[#cfe4fc] shadow-md w-[330px] min-w-[250px]" // Use theme colors
          >
            <h3 className="text-primary lg:text-4xl md:text-3xl text-2xl mb-1">{stat.value}</h3>{" "}
            {/* Use theme primary color */}
            <h3 className="text-foreground lg:text-3xl md:text-2xl text-xl">{stat.label}</h3>{" "}
            {/* Use theme foreground color */}
          </div>
        ))}
      </div>
    </div>
    </div>
  );
};

export default StatisticsSection;
