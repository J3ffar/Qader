"use client";

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
import { queryKeys } from "@/constants/queryKeys";
import { createPost } from "@/services/community.service";
import { CreatePostPayload } from "@/types/api/community.types";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const createPostSchema = z.object({
  content: z
    .string()
    .min(10, "يجب أن يحتوي المنشور على 10 أحرف على الأقل.")
    .max(5000),
  // Add other fields like image, title etc.
});

export function CreatePostDialog() {
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();

  const form = useForm<z.infer<typeof createPostSchema>>({
    resolver: zodResolver(createPostSchema),
    defaultValues: { content: "" },
  });

  const mutation = useMutation({
    mutationFn: (payload: CreatePostPayload) => createPost(payload),
    onSuccess: () => {
      toast.success("تم نشر مناقشتك بنجاح!");
      queryClient.invalidateQueries({
        queryKey: queryKeys.community.posts.lists(),
      });
      setIsOpen(false);
      form.reset();
    },
    onError: (error) => {
      toast.error("فشل في نشر المناقشة. يرجى المحاولة مرة أخرى.", {
        description: error.message,
      });
    },
  });

  const onSubmit = (values: z.infer<typeof createPostSchema>) => {
    mutation.mutate({ ...values, post_type: "discussion" }); // Assuming discussion for now
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button>نشر مناقشة</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>إنشاء منشور جديد</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="content"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>محتوى المنشور</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="ما الذي تفكر به؟"
                      {...field}
                      rows={6}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {/* Add file input for image here */}
            <Button
              type="submit"
              className="w-full"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? "جاري النشر..." : "نشر"}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
