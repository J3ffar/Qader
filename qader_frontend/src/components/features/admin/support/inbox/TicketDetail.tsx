"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { useTranslations } from "next-intl";
import { Send, Info, Lock, Paperclip, Mail } from "lucide-react";

import {
  getSupportTicketDetail,
  addTicketReply,
  updateSupportTicket,
} from "@/services/api/admin/support.service";
import { queryKeys } from "@/constants/queryKeys";
import { TicketDetailSkeleton } from "./TicketDetailSkeleton";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import type {
  SimpleUser,
  SupportTicketReply,
  TicketPriority,
  TicketStatus,
} from "@/types/api/admin/support.types";

// Placeholder when no ticket is selected
function SelectTicketPlaceholder() {
  const t = useTranslations("Admin.support.inbox");
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
      <Mail className="h-16 w-16" />
      <h2 className="text-2xl font-bold">{t("selectTicketTitle")}</h2>
      <p>{t("selectTicketDescription")}</p>
    </div>
  );
}

// Reply form schema
const replySchema = z.object({
  message: z.string().min(1, "Message cannot be empty."),
});

export function TicketDetail({ ticketId }: { ticketId: number | null }) {
  const queryClient = useQueryClient();
  const t = useTranslations("Admin.support");
  const tStatus = useTranslations("Admin.support.statusLabels");
  const tPriority = useTranslations("Admin.support.priorityLabels");

  // Fetch ticket details, only runs if ticketId is not null
  const {
    data: ticket,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.admin.support.detail(ticketId!),
    queryFn: () => getSupportTicketDetail(ticketId!),
    enabled: !!ticketId,
  });

  // Mutation for sending a reply
  const { mutate: sendReply, isPending: isReplying } = useMutation({
    mutationFn: (values: { message: string }) =>
      addTicketReply(ticketId!, values),
    onSuccess: (newReply) => {
      toast.success(t("actions.replySuccess"));
      queryClient.setQueryData(
        queryKeys.admin.support.detail(ticketId!),
        (oldData: any) => ({
          ...oldData,
          replies: [...oldData.replies, newReply],
        })
      );
      form.reset();
    },
    onError: () => toast.error(t("actions.replyError")),
  });

  // Mutation for updating status or priority
  const { mutate: updateTicket } = useMutation({
    mutationFn: (payload: {
      status?: TicketStatus;
      priority?: TicketPriority;
    }) => updateSupportTicket(ticketId!, payload),
    onSuccess: (updatedData) => {
      toast.success(t("actions.updateSuccess"));
      queryClient.setQueryData(
        queryKeys.admin.support.detail(ticketId!),
        (oldData: any) => ({
          ...oldData,
          ...updatedData,
        })
      );
      // Invalidate list to update status/priority there too
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.support.lists(),
      });
    },
    onError: () => toast.error(t("actions.updateError")),
  });

  const form = useForm<z.infer<typeof replySchema>>({
    resolver: zodResolver(replySchema),
    defaultValues: { message: "" },
  });

  if (!ticketId) return <SelectTicketPlaceholder />;
  if (isLoading) return <TicketDetailSkeleton />;
  if (isError)
    return <div className="p-4 text-destructive">{t("errors.fetchError")}</div>;
  if (!ticket) return null; // Should be covered by error state

  const onSubmit = (values: z.infer<typeof replySchema>) => {
    sendReply(values);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with actions */}
      <div className="flex items-center p-2 border-b">
        <div className="flex items-center gap-2">
          <Avatar>
            <AvatarImage
              src={ticket.user.profile_picture_url || ""}
              alt={ticket.user.username}
            />
            <AvatarFallback>
              {ticket.user.username.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="grid gap-0.5">
            <p className="font-semibold">{ticket.user.full_name}</p>
            <p className="text-xs text-muted-foreground">{ticket.user.email}</p>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Select
            value={ticket.status}
            onValueChange={(v: TicketStatus) => updateTicket({ status: v })}
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {["open", "pending_admin", "pending_user", "closed"].map((s) => (
                <SelectItem key={s} value={s}>
                  {tStatus(s)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={String(ticket.priority)}
            onValueChange={(v: string) =>
              updateTicket({ priority: Number(v) as TicketPriority })
            }
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[1, 2, 3].map((p) => (
                <SelectItem key={p} value={String(p)}>
                  {tPriority(String(p))}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Chat messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Original Message */}
        <div className="p-4 rounded-lg bg-muted">
          <h3 className="font-bold mb-2">{ticket.subject}</h3>
          <p className="text-sm whitespace-pre-wrap">{ticket.description}</p>
          {ticket.attachment && (
            <a
              href={ticket.attachment}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-2 text-sm text-blue-500 hover:underline"
            >
              <Paperclip className="h-4 w-4" /> View Attachment
            </a>
          )}
        </div>
        <Separator />
        {/* Replies */}
        {ticket.replies.map((reply) => (
          <ChatMessage
            key={reply.id}
            reply={reply}
            currentUser={ticket.assigned_to}
          />
        ))}
      </div>

      {/* Reply Form */}
      <div className="p-4 border-t bg-background">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="relative">
            <Textarea
              placeholder={t("inbox.replyPlaceholder")}
              className="min-h-12 resize-none pr-16"
              {...form.register("message")}
            />
            <Button
              type="submit"
              size="icon"
              className="absolute top-3 right-3"
              disabled={isReplying}
            >
              <Send className="h-4 w-4" />
            </Button>
            <FormMessage>{form.formState.errors.message?.message}</FormMessage>
          </form>
          {/* Add a button for internal notes here if needed */}
        </Form>
      </div>
    </div>
  );
}

// Chat Message bubble component
function ChatMessage({
  reply,
  currentUser,
}: {
  reply: SupportTicketReply;
  currentUser: SimpleUser | null;
}) {
  const isAdminReply = currentUser ? reply.user.id !== currentUser.id : false;

  if (reply.is_internal_note) {
    return (
      <div className="flex items-start gap-3 p-3 rounded-lg bg-yellow-100 dark:bg-yellow-900/50 border border-yellow-200 dark:border-yellow-800">
        <Lock className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-1" />
        <div>
          <p className="font-bold text-sm">
            Internal Note by {reply.user.username}
          </p>
          <p className="text-sm whitespace-pre-wrap">{reply.message}</p>
          <p className="text-xs text-muted-foreground mt-1">
            {new Date(reply.created_at).toLocaleString()}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex items-end gap-3", !isAdminReply && "justify-end")}>
      {isAdminReply && (
        <Avatar className="h-8 w-8">
          <AvatarImage src={reply.user.profile_picture_url || ""} />
          <AvatarFallback>
            {reply.user.username.charAt(0).toUpperCase()}
          </AvatarFallback>
        </Avatar>
      )}
      <div
        className={cn(
          "max-w-md p-3 rounded-lg",
          isAdminReply ? "bg-muted" : "bg-primary text-primary-foreground"
        )}
      >
        <p className="text-sm whitespace-pre-wrap">{reply.message}</p>
      </div>
      {!isAdminReply && (
        <Avatar className="h-8 w-8">
          <AvatarImage src={reply.user.profile_picture_url || ""} />
          <AvatarFallback>
            {reply.user.username.charAt(0).toUpperCase()}
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}
