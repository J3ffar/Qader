"use client";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Send } from "lucide-react";
import { useTranslations } from "next-intl";
import * as z from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

const schema = z.object({
  issueType: z.string().min(1, { message: "Please select an issue type" }),
  description: z.string().min(1, { message: "Please describe your issue" }),
});

export default function ReportProblemForm() {
  const t = useTranslations("Study.emergencyMode.session");

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    mode: "onChange",
    defaultValues: {
      issueType: "",
      description: "",
    },
  });

  const {
    control,
    handleSubmit,
    formState: { isValid },
  } = form;

  // TODO: Replace with actual submission logic
  const onSubmit = (data: z.infer<typeof schema>) => {
    console.log("Report submitted:", data);
  };

  return (
    <Form {...form}>
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-4 p-4 rounded-2xl shadow-sm"
      >
        {/* Issue Type */}
        <FormField
          control={control}
          name="issueType"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="font-semibold text-gray-700">
                {t("issueTypeLabel")}
              </FormLabel>
              <FormControl>
                <select
                  {...field}
                  className="w-full border rounded px-3 py-2 focus:outline-none"
                >
                  <option value="" disabled>
                    {t("selectIssueTypeLabel")}
                  </option>
                  <option value="technical">{t("issueTypeTechnical")}</option>
                  <option value="other">{t("issueTypeOther")}</option>
                </select>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Description */}
        <FormField
          control={control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="font-semibold text-gray-700">
                {t("requestDescriptionLabel")}
              </FormLabel>
              <FormControl>
                <Textarea
                  {...field}
                  className="w-full border h-36 resize-none rounded px-3 py-2 focus:outline-none"
                  placeholder={t("requestDescriptionPlaceholder")}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Submit Button */}
        <Button
          type="submit"
          className="w-full font-bold py-2 rounded flex items-center justify-center gap-2"
          disabled={!isValid}
        >
          {t("send")}
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </Form>
  );
}
