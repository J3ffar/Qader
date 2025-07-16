import { Button } from "@/components/ui/button";
import { Minus, Plus } from "lucide-react";
import { useState } from "react";
import { useTranslations } from "next-intl";

export function EmergencyModeActivitationForm() {
  const t = useTranslations("Study.emergencyMode.setup");
  const [remainingDays, setRemainingDays] = useState(1);
  const [hoursPerDay, setHoursPerDay] = useState(1);
  // Remaining Days Handlers
  const handleRemainingDaysChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const val = e.target.value;
    if (val === "") {
      setRemainingDays(0);
    } else {
      const num = Number(val);
      if (!isNaN(num) && num >= 0) {
        setRemainingDays(num);
      }
    }
  };
  const handleRemainingDaysIncrement = () => {
    setRemainingDays((prev) => prev + 1);
  };
  const handleRemainingDaysDecrement = () => {
    setRemainingDays((prev) => Math.max(0, prev - 1));
  };

  // Time Per Day Handlers
  const handleHoursChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (val === "") {
      setHoursPerDay(0);
    } else {
      const num = Number(val);
      if (!isNaN(num) && num >= 1) {
        setHoursPerDay(Math.min(24, num));
      }
    }
  };

  const handleHourIncrement = () => {
    setHoursPerDay((prev) => Math.min(24, prev + 1));
  };
  const handleHourDecrement = () => {
    setHoursPerDay((prev) => Math.max(1, prev - 1));
  };
  return (
    <form action="" className="flex flex-col gap-2 py-4 text-xs min-w-0">
      <div className="flex flex-col md:flex-row justify-between gap-4 items-stretch">
        {/* Remaining Days */}
        <div className="flex flex-col bg-gray-100 border rounded w-full md:w-1/2">
          <p className="font-semibold text-sm mx-4 my-5">
            {t("remainingDaysLabel")}
          </p>
          <div className="bg-white flex items-center justify-center gap-4 p-4 flex-1">
            <div className="text-2xl flex items-center justify-center w-full">
              <button
                className="px-3 py-1 hover:cursor-pointer text-[#074182]"
                onClick={handleRemainingDaysDecrement}
                type="button"
              >
                <Minus />
              </button>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={remainingDays}
                onChange={handleRemainingDaysChange}
                className="w-16 md:w-20 border border-gray-300 text-blue-900 font-bold rounded px-2 py-1 text-center"
              />
              <button
                className="px-3 py-1 hover:cursor-pointer text-[#074182]"
                onClick={handleRemainingDaysIncrement}
                type="button"
              >
                <Plus />
              </button>
            </div>
          </div>
        </div>

        {/* Hours Per Day */}
        <div className="flex flex-col bg-gray-100 border rounded w-full md:w-1/2 mt-4 md:mt-0">
          <p className="font-semibold text-sm mx-4 my-5">
            {t("hoursPerDayLabel")}
          </p>
          <div className="bg-white flex items-center justify-center gap-4 p-4 flex-1">
            <div className="text-2xl flex items-center justify-center w-full">
              <button
                onClick={handleHourDecrement}
                className="px-3 py-1 hover:cursor-pointer text-[#074182]"
                aria-label="Increment hours"
              >
                <Minus />
              </button>

              <div className="flex items-center gap-2 justify-center">
                {/* Minutes Input */}
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  value={"00"}
                  readOnly
                  className="w-12 sm:w-16 md:w-20 bg-gray-100 text-blue-900 font-bold rounded px-2 py-1 text-center"
                  min={0}
                  max={59}
                />

                {/* Dots */}
                <span className="text-2xl font-bold text-black flex flex-col items-center">
                  <span className="leading-none ">.</span>
                  <span className="leading-none">.</span>
                </span>

                {/* Hours Input */}
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  value={hoursPerDay}
                  onChange={handleHoursChange}
                  className="w-12 sm:w-16 md:w-20 bg-blue-100 text-blue-900 font-bold rounded px-2 py-1 text-center"
                  min={1}
                  max={24}
                />
              </div>

              <button
                onClick={handleHourIncrement}
                className="px-3 py-1 hover:cursor-pointer text-[#074182]"
                aria-label="Decrement hours"
              >
                <Plus />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Button below */}
      <Button className="w-full sm:w-[258px] text-lg mx-auto rounded-md py-6 px-4 hover:cursor-pointer mt-4">
        {t("activate")}
      </Button>
    </form>
  );
}
