// src/components/features/platform/support/CreateSupportTicketForm.tsx
"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { createSupportTicket } from "@/services/support.service";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Paperclip, Send } from "lucide-react";
import { useRef } from "react";

const formSchema = z.object({
  issue_type: z.enum(["technical", "financial", "question_problem", "other"], {
    required_error: "نوع المشكلة مطلوب.",
  }),
  subject: z.string().min(5, "يجب أن يكون الموضوع 5 أحرف على الأقل.").max(100),
  description: z
    .string()
    .min(10, "يجب أن يكون الوصف 10 أحرف على الأقل.")
    .max(1000),
  attachment: z.instanceof(File).optional().nullable(),
});

const issueTypeTranslations: { [key: string]: string } = {
  technical: "مشكلة تقنية",
  financial: "مشكلة مالية",
  question_problem: "مشكلة في سؤال",
  other: "أخرى",
};

export function CreateSupportTicketForm() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { subject: "", description: "" },
  });

  const createTicketMutation = useMutation({
    mutationFn: createSupportTicket,
    onSuccess: () => {
      toast.success("تم إرسال تذكرتك بنجاح!");
      queryClient.invalidateQueries({
        queryKey: queryKeys.user.support.lists(),
      });
      form.reset();
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "فشل إرسال التذكرة."));
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    createTicketMutation.mutate(values);
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-6"
        dir="rtl"
      >
        {/* All fields go here */}
        <FormField
          control={form.control}
          name="subject"
          render={({ field }) => (
            <FormItem>
              <FormLabel>الموضوع</FormLabel>
              <FormControl>
                <Input placeholder="مثال: أحتاج مساعدة في..." {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="issue_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>نوع المشكلة</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="اختر نوع المشكلة" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {Object.entries(issueTypeTranslations).map(([key, value]) => (
                    <SelectItem key={key} value={key}>
                      {value}
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
              <FormLabel>وصف المشكلة</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="يرجى توضيح المشكلة بالتفصيل..."
                  className="min-h-[120px]"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="attachment"
          render={({ field }) => (
            <FormItem>
              <FormLabel>إرفاق ملف (اختياري)</FormLabel>
              <FormControl>
                <div className="flex items-center gap-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Paperclip className="rtl:ml-2 ltr:mr-2 h-4 w-4" /> ارفق
                    صورة هنا
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    {field.value?.name ?? "لم يتم اختيار ملف."}
                  </span>
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    onChange={(e) =>
                      field.onChange(e.target.files ? e.target.files[0] : null)
                    }
                  />
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button
          type="submit"
          className="w-full"
          disabled={createTicketMutation.isPending}
        >
          {createTicketMutation.isPending ? "جاري الإرسال..." : "إرسال"}
          <Send className="rtl:mr-2 ltr:ml-2 h-4 w-4" />
        </Button>
      </form>
    </Form>
  );
}
