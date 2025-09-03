"use client";

import { Button } from "@/components/ui/button";
import { Loader2, Minus, Plus } from "lucide-react";
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
import { Input } from "@/components/ui/input";
import Image from "next/image";

interface Props {
  onSubmit: (data: FormValues) => void;
  isPending: boolean;
  maxHours?: number;
  maxDays?: number;
  minDays?: number;
}

// Create schema function that accepts validation limits
const createEmergencyActivationSchema = (maxHours = 16, maxDays = 14, minDays = 1) => {
  return z.object({
    days_until_test: z.coerce
      .number()
      .min(minDays, { message: `يجب أن يكون عدد الأيام المتبقية للامتحان ${minDays} يوم على الأقل` })
      .max(maxDays, { message: `لا يمكن أن يتجاوز عدد الأيام المتبقية للامتحان ${maxDays} يوم` }),
    available_time_hours: z.coerce
      .number()
      .min(0, { message: "يجب أن تكون الساعات صفر على الأقل" })
      .max(maxHours, { message: `لا يمكن أن تتجاوز ساعات الدراسة المتاحة ${maxHours} ساعة في اليوم` }),
    available_time_minutes: z.coerce
      .number()
      .min(0, { message: "يجب أن تكون الدقائق صفر على الأقل" })
      .max(59, { message: "لا يمكن أن تتجاوز الدقائق 59 دقيقة" }),
  }).refine(
    (data) => data.available_time_hours > 0 || data.available_time_minutes > 0,
    {
      message: "يجب أن يكون الوقت المتاح أكثر من صفر",
      path: ["available_time_hours"],
    }
  );
};

type FormValues = z.infer<ReturnType<typeof createEmergencyActivationSchema>>;

export default function EmergencyModeActivitationForm({
  onSubmit,
  isPending,
  maxHours = 16,
  maxDays = 14,
  minDays = 1,
}: Props) {
  const t = useTranslations("Study.emergencyMode.setup");
  
  // Create schema with validation limits
  const emergencyActivationSchema = createEmergencyActivationSchema(maxHours, maxDays, minDays);
  
  const form = useForm<FormValues>({
    resolver: zodResolver(emergencyActivationSchema),
    defaultValues: {
      days_until_test: minDays,
      available_time_hours: 1,
      available_time_minutes: 0,
    },
  });

  const { watch, setValue } = form;
  const days = watch("days_until_test");
  const hours = watch("available_time_hours");
  const minutes = watch("available_time_minutes");

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-4 py-4 min-w-0"
      >
        {/* Reverting to the client-requested two-box layout */}
        <div className="flex flex-col md:flex-row justify-between gap-4 items-stretch">
          {/* Remaining Days Box */}
          <FormField
            control={form.control}
            name="days_until_test"
            render={() => (
              <FormItem className="flex flex-col bg-gray-100 dark:bg-card border rounded-xl w-full md:w-1/2 p-0">
                <FormLabel className="font-semibold text-sm mx-4 my-5 rtl:text-right">
                  {t("remainingDaysLabel")}
                  <span className="text-xs text-muted-foreground block mt-1">
                    (الحد الأدنى: {minDays} يوم، الحد الأقصى: {maxDays} يوم)
                  </span>
                </FormLabel>
                <FormControl>
                  <div className="bg-background flex items-center justify-center gap-4 p-4 flex-1 rounded-b-xl">
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() =>
                        setValue("days_until_test", Math.max(minDays, days - 1))
                      }
                      disabled={days <= minDays}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                    <Input
                      type="number"
                      className="w-20 h-10 text-center font-bold text-lg"
                      value={days}
                      min={minDays}
                      max={maxDays}
                      onChange={(e) => {
                        const value = Number(e.target.value);
                        if (value >= minDays && value <= maxDays) {
                          setValue("days_until_test", value);
                        }
                      }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() =>
                        setValue("days_until_test", Math.min(maxDays, days + 1))
                      }
                      disabled={days >= maxDays}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </FormControl>
                <FormMessage className="p-2" />
              </FormItem>
            )}
          />

          {/* Available Hours Box */}
          <FormField
            control={form.control}
            name="available_time_hours"
            render={() => (
              <FormItem className="flex flex-col bg-gray-100 dark:bg-card border rounded-xl w-full md:w-1/2 p-0">
                <FormLabel className="font-semibold text-sm mx-4 my-5 rtl:text-right">
                  {t("availableHoursLabel")}
                  <span className="text-xs text-muted-foreground block mt-1">
                    (الحد الأقصى: {maxHours} ساعة، 59 دقيقة)
                  </span>
                </FormLabel>
                <FormControl>
                  <div className="bg-background flex items-center justify-center gap-4 p-4 flex-1 rounded-b-xl">
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() => {
                        if (minutes > 0) {
                          setValue("available_time_minutes", minutes - 1);
                        } else if (hours > 0) {
                          setValue("available_time_hours", hours - 1);
                          setValue("available_time_minutes", 59);
                        }
                      }}
                      disabled={hours <= 0 && minutes <= 0}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                    <div className="flex items-center gap-2 justify-center">
                      <Input
                        type="number"
                        className="w-20 h-10 text-center font-bold text-lg"
                        value={minutes.toString().padStart(2, '0')}
                        min={0}
                        max={59}
                        onChange={(e) => {
                          const value = Number(e.target.value);
                          if (value >= 0 && value <= 59) {
                            setValue("available_time_minutes", value);
                          }
                        }}
                      />
                      <span className="text-2xl font-bold text-black flex flex-col items-center">
                        <span className="leading-none">.</span>
                        <span className="leading-none">.</span>
                      </span>
                      <Input
                        type="number"
                        className="w-20 h-10 text-center font-bold text-lg"
                        value={hours.toString().padStart(2, '0')}
                        min={0}
                        max={maxHours}
                        onChange={(e) => {
                          const value = Number(e.target.value);
                          if (value >= 0 && value <= maxHours) {
                            setValue("available_time_hours", value);
                          }
                        }}
                      />
                    </div>

                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() => {
                        if (minutes < 59) {
                          setValue("available_time_minutes", minutes + 1);
                        } else if (hours < maxHours) {
                          setValue("available_time_hours", hours + 1);
                          setValue("available_time_minutes", 0);
                        }
                      }}
                      disabled={hours >= maxHours && minutes >= 59}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </FormControl>
                <FormMessage className="p-2" />
              </FormItem>
            )}
          />
        </div>
        <div className="flex justify-center items-center flex-col pt-4">
          <Image
            src="/images/search.png"
            alt="Document illustration"
            width={150}
            height={200}
            className="object-contain my-4"
          />
          <div className="text-center space-y-2">
            <p className="font-semibold text-2xl">{t("selectDaysAndHours")}</p>
            <p className="text-muted-foreground">{t("needToSelect")}</p>
          </div>
        </div>
        {/* Submit Button */}
        <Button
          type="submit"
          className="w-full sm:w-[258px] text-lg mx-auto rounded-md py-6 px-4 mt-4"
          disabled={isPending}
        >
          {isPending && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin rtl:ml-2" />
          )}
          {t("activate")}
        </Button>
      </form>
    </Form>
  );
}
