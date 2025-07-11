"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";

import { Form, FormControl, FormField, FormItem } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { createReply } from "@/services/community.service";
import { queryKeys } from "@/constants/queryKeys";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuthStore } from "@/store/auth.store";
import { Loader2 } from "lucide-react";

const replySchema = z.object({
  content: z.string().min(1, "لا يمكن أن يكون الرد فارغًا.").max(1000),
});

interface CreateReplyFormProps {
  postId: number;
  parentReplyId?: number;
  onReplySuccess?: () => void;
  isClosed: boolean;
  autoFocus?: boolean;
}

export function CreateReplyForm({
  postId,
  parentReplyId,
  onReplySuccess,
  isClosed,
  autoFocus,
}: CreateReplyFormProps) {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);

  const form = useForm<z.infer<typeof replySchema>>({
    resolver: zodResolver(replySchema),
    defaultValues: { content: "" },
  });

  const mutation = useMutation({
    mutationFn: (values: { content: string }) =>
      createReply({ postId, content: values.content, parentReplyId }),
    onSuccess: () => {
      toast.success("تم إرسال ردك بنجاح.");
      // Invalidate both the replies list and the main post list (to update reply_count)
      queryClient.invalidateQueries({
        queryKey: queryKeys.community.postDetails.replies(postId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.community.posts.lists(),
      });
      form.reset();
      onReplySuccess?.();
    },
    onError: (error) => {
      toast.error("فشل إرسال الرد.", { description: error.message });
    },
  });

  const onSubmit = (values: z.infer<typeof replySchema>) => {
    if (isClosed) return;
    mutation.mutate(values);
  };

  if (isClosed && !parentReplyId) {
    // Only show the main "closed" message on the top-level form
    return (
      <div className="text-center text-sm text-muted-foreground p-4 bg-muted rounded-md">
        هذه المناقشة مغلقة ولا يمكن إضافة ردود جديدة.
      </div>
    );
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="w-full flex items-center space-x-2 rtl:space-x-reverse py-2"
      >
        <Avatar className="h-9 w-9">
          <AvatarImage src={user?.profile_picture_url || undefined} />
          <AvatarFallback>
            {user?.preferred_name?.charAt(0) || "U"}
          </AvatarFallback>
        </Avatar>
        <FormField
          control={form.control}
          name="content"
          render={({ field }) => (
            <FormItem className="flex-1">
              <FormControl>
                <Input
                  placeholder="اكتب ردًا..."
                  {...field}
                  disabled={mutation.isPending || isClosed}
                  autoFocus={autoFocus}
                />
              </FormControl>
            </FormItem>
          )}
        />
        <Button
          type="submit"
          size="sm"
          disabled={mutation.isPending || isClosed}
        >
          {mutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            "إرسال"
          )}
        </Button>
      </form>
    </Form>
  );
}
