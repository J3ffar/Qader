"use client";

import { useForm } from "react-hook-form";
import * as z from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

import { queryKeys } from "@/constants/queryKeys";
import { requestEmergencySupport } from "@/services/study.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

const problemTypes = ["technical", "academic", "content", "other"] as const;

const createReportSchema = (t: (key: string) => string) =>
  z.object({
    problem_type: z.enum(problemTypes, {
      required_error: t("problemTypePlaceholder"),
    }),
    description: z.string().min(10, {
      message: t("descriptionLabel"), // A generic message, specific length validation is less common here
    }),
  });

interface ReportProblemFormProps {
  sessionId: any;
  onSuccess?: () => void;
}

export default function ReportProblemForm({
  sessionId,
  onSuccess,
}: ReportProblemFormProps) {
  const t = useTranslations("Study.emergencyMode.session.requestSupport");
  const formSchema = createReportSchema(t);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      description: "",
    },
  });

  const { mutate, isPending } = useMutation({
    mutationKey: queryKeys.emergencyMode.support(sessionId),
    mutationFn: (payload: z.infer<typeof formSchema>) =>
      requestEmergencySupport({ sessionId, payload }),
    onSuccess: () => {
      toast.success(t("successToast"));
      form.reset();
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(t("errorToast"), {
        description: getApiErrorMessage(error, "لقد حدث خطأ في الارسال"),
      });
    },
  });

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit((data) => mutate(data))}
        className="space-y-6"
      >
        <p className="text-sm text-muted-foreground">{t("description")}</p>
        <FormField
          control={form.control}
          name="problem_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t("problemTypeLabel")}</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder={t("problemTypePlaceholder")} />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {problemTypes.map((type) => (
                    <SelectItem key={type} value={type} dir="rtl">
                      {t(type)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t("descriptionLabel")}</FormLabel>
              <FormControl>
                <Textarea
                  placeholder={t("descriptionPlaceholder")}
                  className="resize-none"
                  rows={5}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" disabled={isPending} className="w-full">
          {isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin rtl:ml-2" />
          ) : (
            <Send className="mr-2 h-4 w-4 rtl:ml-2" />
          )}
          {t("sendButton")}
        </Button>
      </form>
    </Form>
  );
}
