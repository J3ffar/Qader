"use client";

import { useState } from "react";
import Image from "next/image";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2, Plus, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { createPost } from "@/services/community.service";
import { queryKeys } from "@/constants/queryKeys";
import { CreatePostPayload, PostType } from "@/types/api/community.types";

const POST_TYPE_CONFIG: Record<
  PostType,
  { title: string; buttonText: string }
> = {
  discussion: { title: "إنشاء مناقشة جديدة", buttonText: "نشر المناقشة" },
  achievement: { title: "مشاركة إنجاز جديد", buttonText: "نشر الإنجاز" },
  tip: { title: "مشاركة نصيحة أو تجربة", buttonText: "نشر النصيحة" },
  competition: { title: "", buttonText: "" },
  partner_search: { title: "", buttonText: "" },
};

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ACCEPTED_IMAGE_TYPES = [
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
];

const createPostSchema = z.object({
  title: z
    .string()
    .max(255, "يجب أن يكون العنوان أقل من 255 حرفًا.")
    .optional(),
  content: z
    .string()
    .min(10, "يجب أن يحتوي المنشور على 10 أحرف على الأقل.")
    .max(5000),
  image: z
    .instanceof(File)
    .optional()
    .refine(
      (file) => !file || file.size <= MAX_FILE_SIZE,
      `يجب أن يكون حجم الصورة أصغر من 5 ميجابايت.`
    )
    .refine(
      (file) => !file || ACCEPTED_IMAGE_TYPES.includes(file.type),
      "تنسيقات الصور المدعومة هي .jpg, .jpeg, .png, .webp"
    ),
  section_filter: z.string().optional(),
});

const SECTIONS = [
  { label: "بدون قسم محدد", value: "none" },
  { label: "القسم اللفظي", value: "verbal" },
  { label: "القسم الكمي", value: "quantitative" },
];

export function CreatePostDialog({ postType }: { postType: PostType }) {
  const [isOpen, setIsOpen] = useState(false);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const config = POST_TYPE_CONFIG[postType];

  const form = useForm<z.infer<typeof createPostSchema>>({
    resolver: zodResolver(createPostSchema),
    defaultValues: {
      title: "",
      content: "",
      image: undefined,
      section_filter: "none",
    },
  });

  const mutation = useMutation({
    mutationFn: (payload: CreatePostPayload) => createPost(payload),
    onSuccess: () => {
      toast.success(config.buttonText.replace("نشر", "تم نشر") + " بنجاح!");
      queryClient.invalidateQueries({
        queryKey: queryKeys.community.posts.list({ post_type: postType }),
      });
      handleClose();
    },
    onError: (error) => {
      toast.error("فشل في نشر المنشور.", { description: error.message });
    },
  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      form.setValue("image", file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const removeImage = () => {
    form.setValue("image", undefined);
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
      setImagePreview(null);
    }
  };

  const handleClose = () => {
    form.reset();
    removeImage();
    setIsOpen(false);
  };

  const onSubmit = (values: z.infer<typeof createPostSchema>) => {
    const payload = {
      ...values,
      post_type: postType,
      title: values.title || undefined,
      image: values.image || undefined,
      section_filter:
        values.section_filter === "none" ? undefined : values.section_filter,
      tags: [],
    };
    mutation.mutate(payload);
  };

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => (open ? setIsOpen(true) : handleClose())}
    >
      <DialogTrigger asChild>
        <Button>
          <Plus className="me-2 h-4 w-4" />
          {config.buttonText.replace("نشر", "نشر ")}
        </Button>
      </DialogTrigger>
      <DialogContent
        className="sm:max-w-[500px]"
        onInteractOutside={(e) => {
          if (mutation.isPending) e.preventDefault();
        }}
      >
        <DialogHeader>
          <DialogTitle>{config.title}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* Title Field */}
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>العنوان (اختياري)</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="أضف عنوانًا مميزًا لمناقشتك"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Content Field */}
            <FormField
              control={form.control}
              name="content"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>المحتوى</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="ما الذي يدور في ذهنك؟"
                      {...field}
                      className="min-h-52"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Section Filter Field */}
            <FormField
              control={form.control}
              name="section_filter"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>القسم (اختياري)</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="حدد القسم المتعلق بالمنشور" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {SECTIONS.map((section) => (
                        <SelectItem key={section.value} value={section.value}>
                          {section.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Image Field */}
            <FormField
              control={form.control}
              name="image"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>إضافة صورة (اختياري)</FormLabel>
                  {imagePreview ? (
                    <div className="relative">
                      <Image
                        src={imagePreview}
                        alt="Preview"
                        width={450}
                        height={250}
                        className="rounded-md object-cover w-full h-auto max-h-64"
                      />
                      <Button
                        type="button"
                        variant="destructive"
                        size="icon"
                        className="absolute top-2 right-2 h-7 w-7"
                        onClick={removeImage}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : (
                    <FormControl>
                      <Input
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                      />
                    </FormControl>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button
              type="submit"
              className="w-full"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? (
                <Loader2 className="me-2 h-4 w-4 animate-spin" />
              ) : null}
              {mutation.isPending ? "جاري النشر..." : config.buttonText}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
