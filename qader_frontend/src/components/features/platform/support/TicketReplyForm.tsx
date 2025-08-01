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
      await queryClient.cancelQueries({
        queryKey: queryKeys.user.support.detail(ticketId),
      });

      const previousTicket = queryClient.getQueryData<SupportTicketDetail>(
        queryKeys.user.support.detail(ticketId)
      );

      if (!currentUser) {
        toast.error("حدث خطأ، المستخدم الحالي غير معروف.");
        return { previousTicket };
      }

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
        status: "sending",
      };

      queryClient.setQueryData<SupportTicketDetail>(
        queryKeys.user.support.detail(ticketId),
        (oldTicketData) => {
          // 'oldTicketData' is the current state in the cache
          if (!oldTicketData) {
            return undefined; // Safety check
          }

          // THIS IS THE KEY: We return a BRAND NEW object.
          return {
            // 1. Spread all properties from the old ticket into the new object.
            ...oldTicketData,

            // 2. Overwrite the 'replies' property with a BRAND NEW array.
            replies: [
              // 3. Spread all the old replies into the new array.
              ...oldTicketData.replies,

              // 4. Add our new optimistic reply to the end of the new array.
              optimisticReply,
            ],
          };
        }
      );

      form.reset();
      return { previousTicket };
    },
    onError: (error, _newReply, context) => {
      toast.error(getApiErrorMessage(error, "فشل إرسال الرد."));

      // We can still revert to the snapshot on error
      if (context?.previousTicket) {
        queryClient.setQueryData(
          queryKeys.user.support.detail(ticketId),
          context.previousTicket
        );
      }
    },
    onSuccess: () => {
      // Invalidate to get the real data from the server and replace the optimistic one
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
                    rows={20}
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
