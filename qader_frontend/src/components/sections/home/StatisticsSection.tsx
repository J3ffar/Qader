import React from "react";

// Define statistics data outside the component
const statsData = [
  { id: 1, value: "+5000", label: "اختبار مكتمل" }, // More specific label
  { id: 2, value: "+10000", label: "سؤال تدريبي" },
  { id: 3, value: "+2000", label: "طالب مسجل" },
];

const StatisticsSection = () => {
  return (
    <div className="flex flex-col justify-center items-center p-9 bg-muted/50 dark:bg-slate-800/50 rounded-lg my-8">
      {" "}
      {/* Added background, margin, rounding */}
      {/* Section Header */}
      <h2 className="text-3xl font-medium mb-2 text-center">
        تعرف على إحصائياتنا
      </h2>{" "}
      {/* Use إ not أ */}
      <p className="text-xl text-muted-foreground mb-8 text-center">
        {" "}
        {/* Use muted foreground, added margin */}
        أرقام نفخر بها وتعكس نجاحنا مع طلابنا. {/* Example text */}
      </p>
      {/* Statistics Cards */}
      <div className="flex justify-center items-center gap-6 md:gap-9 flex-wrap">
        {statsData.map((stat) => (
          <div
            key={stat.id}
            className="p-8 sm:p-10 bg-card rounded-lg text-2xl font-bold flex justify-center items-center flex-col border-2 border-primary shadow-md" // Use theme colors
          >
            <h3 className="text-primary text-3xl mb-1">{stat.value}</h3>{" "}
            {/* Use theme primary color */}
            <h3 className="text-foreground text-xl">{stat.label}</h3>{" "}
            {/* Use theme foreground color */}
          </div>
        ))}
      </div>
    </div>
  );
};

export default StatisticsSection;
