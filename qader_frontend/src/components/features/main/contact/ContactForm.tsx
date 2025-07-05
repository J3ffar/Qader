"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { FolderOpenIcon, PaperAirplaneIcon } from "@heroicons/react/24/outline";
import { apiClient } from "@/services/apiClient";
import { setFormErrorsFromApi } from "@/utils/setFormErrorsFromApi";

// 1. Define the form schema with Zod for validation
const formSchema = z.object({
  full_name: z.string().min(3, "الاسم يجب أن يكون 3 أحرف على الأقل."),
  email: z.string().email("الرجاء إدخال بريد إلكتروني صحيح."),
  subject: z.string().min(5, "الموضوع يجب أن يكون 5 أحرف على الأقل."),
  message: z.string().min(10, "الرسالة يجب أن تكون 10 أحرف على الأقل."),
  attachment: z.instanceof(File).optional().nullable(),
});

type ContactFormValues = z.infer<typeof formSchema>;

export const ContactForm = () => {
  const form = useForm<ContactFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      full_name: "",
      email: "",
      subject: "",
      message: "",
      attachment: null,
    },
  });

  const onSubmit = async (values: ContactFormValues) => {
    const formData = new FormData();
    formData.append("full_name", values.full_name);
    formData.append("email", values.email);
    formData.append("subject", values.subject);
    formData.append("message", values.message);
    if (values.attachment) {
      formData.append("attachment", values.attachment);
    }

    const promise = apiClient("/content/contact-us/", {
      method: "POST",
      body: formData,
      isPublic: true,
    });

    toast.promise(promise, {
      loading: "جاري إرسال الرسالة...",
      success: (data: any) => {
        form.reset(); // Reset form fields on success
        return data.detail || "تم إرسال رسالتك بنجاح!";
      },
      error: (error) => {
        setFormErrorsFromApi(error, form.setError);
        return error.message || "فشل إرسال الرسالة. يرجى التحقق من البيانات.";
      },
    });
  };

  return (
    <div className="max-w-lg mx-auto p-6 bg-white dark:bg-[#0B1739] shadow-xl rounded-lg flex-1">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <FormField
            control={form.control}
            name="full_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>الاسم بالكامل</FormLabel>
                <FormControl>
                  <Input placeholder="ادخل اسمك الكامل" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>البريد الإلكتروني</FormLabel>
                <FormControl>
                  <Input
                    type="email"
                    placeholder="ادخل بريدك الإلكتروني"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="subject"
            render={({ field }) => (
              <FormItem>
                <FormLabel>عنوان الموضوع</FormLabel>
                <FormControl>
                  <Input placeholder="ادخل عنوان الموضوع" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="message"
            render={({ field }) => (
              <FormItem>
                <FormLabel>الرسالة</FormLabel>
                <FormControl>
                  <Textarea
                    placeholder="اكتب رسالتك هنا..."
                    rows={5}
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
            render={({ field: { onChange, value, ...rest } }) => (
              <FormItem>
                <FormLabel>إرفاق ملف (اختياري)</FormLabel>
                <FormControl>
                  <label
                    htmlFor="file-upload"
                    className="flex items-center justify-center gap-2 w-full h-32 px-4 py-6 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-md cursor-pointer hover:border-blue-400 bg-gray-50 dark:bg-transparent transition"
                  >
                    <FolderOpenIcon className="h-6 w-6 text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-400">
                      {value?.name ? value.name : "اختر ملفاً"}
                    </span>
                    <Input
                      id="file-upload"
                      type="file"
                      className="hidden"
                      onChange={(e) =>
                        onChange(e.target.files ? e.target.files[0] : null)
                      }
                      {...rest}
                    />
                  </label>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button
            type="submit"
            className="w-full flex items-center gap-2"
            disabled={form.formState.isSubmitting}
          >
            {form.formState.isSubmitting ? "جاري الإرسال..." : "إرسال"}
            {!form.formState.isSubmitting && (
              <PaperAirplaneIcon className="h-5 w-5" />
            )}
          </Button>
        </form>
      </Form>
    </div>
  );
};
