"use client";

import { Button } from "@/components/ui/button";
import { Minus, Plus } from "lucide-react";
import { useTranslations } from "next-intl";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import * as z from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
interface EmergencyModeActivitationFormProps {
  onSubmit: (data: z.infer<typeof emergencyActivationSchema>) => void;
}
const emergencyActivationSchema = z.object({
  remaining_days: z.coerce
    .number()
    .min(0, { message: "Days must be 0 or more" })
    .max(365, { message: "Too many days" }),
  available_time_hours: z.coerce
    .number()
    .min(1, { message: "Must be at least 1 hour" })
    .max(24, { message: "Max is 24 hours" }),
});

export default function EmergencyModeActivitationForm({
  onSubmit,
}: EmergencyModeActivitationFormProps) {
  const t = useTranslations("Study.emergencyMode.setup");
  const form = useForm<z.infer<typeof emergencyActivationSchema>>({
    resolver: zodResolver(emergencyActivationSchema),
    defaultValues: {
      remaining_days: 1,
      available_time_hours: 1,
    },
  });

  const { watch, setValue } = form;
  const remainingDays = watch("remaining_days");
  const hoursPerDay = watch("available_time_hours");

  // Increment/Decrement handlers
  const handleRemainingDaysChange = (val: number) => {
    setValue("remaining_days", Math.max(0, val));
  };

  const handleHoursChange = (val: number) => {
    setValue("available_time_hours", Math.min(24, Math.max(1, val)));
  };

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-4 py-4 text-xs min-w-0"
      >
        <div className="flex flex-col md:flex-row justify-between gap-4 items-stretch">
          {/* Remaining Days */}
          <FormField
            control={form.control}
            name="remaining_days"
            render={({ field }) => (
              <FormItem className="flex flex-col bg-gray-100 dark:bg-[#7E89AC] border rounded-xl w-full md:w-1/2">
                <FormLabel className="font-semibold text-sm mx-4 my-5">
                  {t("remainingDaysLabel")}
                </FormLabel>
                <FormControl>
                  <div className="bg-white dark:bg-[#0A1739] flex items-center justify-center gap-4 p-4 flex-1">
                    <div className="text-2xl flex items-center justify-center w-full">
                      <button
                        type="button"
                        onClick={() =>
                          handleRemainingDaysChange(remainingDays - 1)
                        }
                        className="px-3 py-1 text-[#074182] dark:text-gray-500 cursor-pointer"
                      >
                        <Minus />
                      </button>
                      <input
                        type="text"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        className="w-16 md:w-20 border border-gray-300 text-blue-900 dark:text-white font-bold rounded px-2 py-1 text-center"
                        value={remainingDays}
                        onChange={(e) =>
                          handleRemainingDaysChange(Number(e.target.value))
                        }
                      />
                      <button
                        type="button"
                        onClick={() =>
                          handleRemainingDaysChange(remainingDays + 1)
                        }
                        className="px-3 py-1 text-[#074182] dark:text-gray-500 cursor-pointer"
                      >
                        <Plus />
                      </button>
                    </div>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Hours Per Day */}
          <FormField
            control={form.control}
            name="available_time_hours"
            render={({ field }) => (
              <FormItem className="flex flex-col bg-gray-100 dark:bg-[#7E89AC] border rounded-xl w-full md:w-1/2 mt-4 md:mt-0">
                <FormLabel className="font-semibold text-sm mx-4 my-5">
                  {t("hoursPerDayLabel")}
                </FormLabel>
                <FormControl>
                  <div className="bg-white dark:bg-[#0A1739] flex items-center justify-center gap-4 p-4 flex-1">
                    <div className="text-2xl flex items-center justify-center w-full">
                      <button
                        type="button"
                        onClick={() => handleHoursChange(hoursPerDay - 1)}
                        className="px-3 py-1 text-[#074182] dark:text-gray-500 cursor-pointer"
                      >
                        <Minus />
                      </button>

                      <div className="flex items-center gap-2 justify-center">
                        <input
                          type="text"
                          value="00"
                          readOnly
                          className="w-12 sm:w-16 md:w-20 bg-gray-100 text-black font-bold rounded px-2 py-1 text-center"
                        />
                        <span className="text-2xl font-bold text-black flex flex-col items-center">
                          <span className="leading-none">.</span>
                          <span className="leading-none">.</span>
                        </span>
                        <input
                          type="text"
                          inputMode="numeric"
                          pattern="[0-9]*"
                          readOnly
                          value={hoursPerDay}
                          onChange={(e) =>
                            handleHoursChange(Number(e.target.value))
                          }
                          className="w-12 sm:w-16 md:w-20 bg-blue-100 text-blue-900 font-bold rounded px-2 py-1 text-center"
                        />
                      </div>

                      <button
                        type="button"
                        onClick={() => handleHoursChange(hoursPerDay + 1)}
                        className="px-3 py-1 text-[#074182] dark:text-gray-500 cursor-pointer"
                      >
                        <Plus />
                      </button>
                    </div>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          className="w-full sm:w-[258px] text-lg mx-auto rounded-md py-6 px-4 mt-4 cursor-pointer"
        >
          {t("activate")}
        </Button>
      </form>
    </Form>
  );
}
