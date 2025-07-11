// src/components/features/platform/support/TicketReplyForm.tsx
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
  FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { addTicketReply } from "@/services/support.service";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Send } from "lucide-react";
import type {
  OptimisticSupportTicketReply,
  SupportTicketDetail,
} from "@/types/api/support.types";
import { useAuthStore } from "@/store/auth.store";

const formSchema = z.object({
  message: z.string().min(1, "لا يمكن إرسال رسالة فارغة."),
});

interface TicketReplyFormProps {
  ticketId: number | string;
  isTicketClosed: boolean;
}

export function TicketReplyForm({
  ticketId,
  isTicketClosed,
}: TicketReplyFormProps) {
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((state) => state.user);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { message: "" },
  });

  const addReplyMutation = useMutation({
    mutationFn: (payload: { message: string }) =>
      addTicketReply({ ticketId, payload }),
    onMutate: async (newReply) => {
      // 1. Cancel any outgoing refetches to avoid overwriting our optimistic update
      await queryClient.cancelQueries({
        queryKey: queryKeys.user.support.detail(ticketId),
      });

      // 2. Snapshot the previous value
      const previousTicket = queryClient.getQueryData<SupportTicketDetail>(
        queryKeys.user.support.detail(ticketId)
      );

      // 3. Optimistically update to the new value
      if (previousTicket && currentUser) {
        const optimisticReply: OptimisticSupportTicketReply = {
          id: Date.now(),
          message: newReply.message,
          user: {
            id: currentUser.id,
            username: currentUser.username,
            full_name: currentUser.full_name,
            preferred_name: currentUser.preferred_name,
            profile_picture_url: currentUser.profile_picture_url,
            grade: currentUser.grade,
          },
          created_at: new Date().toISOString(),
          optimistic: true,
        };

        queryClient.setQueryData(queryKeys.user.support.detail(ticketId), {
          ...previousTicket,
          replies: [...previousTicket.replies, optimisticReply],
        });
      }

      form.reset();
      return { previousTicket };
    },
    onError: (error, _newReply, context) => {
      // 4. Rollback to the previous state on error
      if (context?.previousTicket) {
        queryClient.setQueryData(
          queryKeys.user.support.detail(ticketId),
          context.previousTicket
        );
      }
      toast.error(getApiErrorMessage(error, "فشل إرسال الرد."));
    },
    onSettled: () => {
      // 5. Always refetch after error or success to ensure data consistency
      queryClient.invalidateQueries({
        queryKey: queryKeys.user.support.detail(ticketId),
      });
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    if (!currentUser) return toast.error("يجب تسجيل الدخول لإرسال رد.");
    addReplyMutation.mutate(values);
  }

  if (isTicketClosed) {
    return (
      <div className="p-4 border-t text-center bg-muted">
        <p className="text-muted-foreground">
          تم إغلاق هذه المحادثة ولا يمكن إضافة ردود جديدة.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 border-t bg-card">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex items-start gap-4"
          dir="rtl"
        >
          <FormField
            control={form.control}
            name="message"
            render={({ field }) => (
              <FormItem className="flex-1">
                <FormControl>
                  <Textarea
                    placeholder="اكتب رسالتك هنا..."
                    {...field}
                    className="min-h-[40px] resize-none"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        form.handleSubmit(onSubmit)();
                      }
                    }}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="submit" disabled={addReplyMutation.isPending}>
            <Send className="h-5 w-5" />
          </Button>
        </form>
      </Form>
    </div>
  );
}
