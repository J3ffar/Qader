"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import {
  Send,
  Lock,
  Paperclip,
  Mail,
  ArrowLeft,
  MessageSquare,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import type {
  SimpleUser,
  SupportTicketReply,
  TicketPriority,
  TicketStatus,
  AddReplyRequest,
  SupportTicketDetail as TicketDetailType,
} from "@/types/api/admin/support.types";

// Placeholder remains unchanged but is now exported for use in the layout
export function SelectTicketPlaceholder() {
  const t = useTranslations("Admin.support.inbox");
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground p-4">
      <Mail className="h-16 w-16" />
      <h2 className="text-2xl font-bold">{t("selectTicketTitle")}</h2>
      <p>{t("selectTicketDescription")}</p>
    </div>
  );
}

const replySchema = z.object({
  message: z.string().min(1, "Message cannot be empty."),
});

type ReplyFormValues = z.infer<typeof replySchema>;

export function TicketDetail({ ticketId }: { ticketId: number | null }) {
  const queryClient = useQueryClient();
  const t = useTranslations("Admin.support");
  const tInbox = useTranslations("Admin.support.inbox");
  const tStatus = useTranslations("Admin.support.statusLabels");
  const tPriority = useTranslations("Admin.support.priorityLabels");

  const pathname = usePathname();
  const searchParams = useSearchParams();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [replyMode, setReplyMode] = useState<"public" | "internal">("public");

  const {
    data: ticket,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.admin.support.detail(ticketId!),
    queryFn: () => getSupportTicketDetail(ticketId!),
    enabled: !!ticketId,
  });

  const { mutate: sendReply, isPending: isReplying } = useMutation({
    mutationFn: (values: AddReplyRequest) => addTicketReply(ticketId!, values),
    onSuccess: (newReply) => {
      toast.success(t("actions.replySuccess"));
      queryClient.setQueryData<TicketDetailType>(
        queryKeys.admin.support.detail(ticketId!),
        (oldData) => {
          if (!oldData) return undefined;
          return {
            ...oldData,
            replies: [...oldData.replies, newReply],
          };
        }
      );
      form.reset();
    },
    onError: () => toast.error(t("actions.replyError")),
  });

  const { mutate: updateTicket } = useMutation({
    mutationFn: (payload: {
      status?: TicketStatus;
      priority?: TicketPriority;
    }) => updateSupportTicket(ticketId!, payload),
    onSuccess: (updatedData) => {
      toast.success(t("actions.updateSuccess"));
      queryClient.setQueryData(
        queryKeys.admin.support.detail(ticketId!),
        (oldData: any) => ({ ...oldData, ...updatedData })
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.support.lists(),
      });
    },
    onError: () => toast.error(t("actions.updateError")),
  });

  const form = useForm<ReplyFormValues>({
    resolver: zodResolver(replySchema),
    defaultValues: { message: "" },
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (ticket?.replies) {
      scrollToBottom();
    }
  }, [ticket?.replies]);

  const createBackLink = () => {
    const params = new URLSearchParams(searchParams);
    params.delete("ticket");
    return `${pathname}?${params.toString()}`;
  };

  const onSubmit = (values: ReplyFormValues) => {
    sendReply({
      message: values.message,
      is_internal_note: replyMode === "internal",
    });
  };

  if (!ticketId) return null; // Handled by layout
  if (isLoading) return <TicketDetailSkeleton />;
  if (isError)
    return <div className="p-4 text-destructive">{t("errors.fetchError")}</div>;
  if (!ticket) return null;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center p-2 border-b">
        <Link href={createBackLink()} className="md:hidden p-2 mr-2">
          <ArrowLeft className="h-5 w-5" />
          <span className="sr-only">Back to list</span>
        </Link>
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
        <div className="ms-auto flex items-center gap-2">
          <Select
            value={ticket.status}
            onValueChange={(v: TicketStatus) => updateTicket({ status: v })}
          >
            <SelectTrigger className="w-auto md:w-[150px]">
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
            <SelectTrigger className="w-auto md:w-[150px]">
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

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="p-4 rounded-lg bg-muted">
          <h3 className="font-bold mb-2">{ticket.subject}</h3>
          <p className="text-sm whitespace-pre-wrap">{ticket.description}</p>
          {ticket.attachment && (
            <a
              href={ticket.attachment}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-2 text-sm text-primary hover:underline"
            >
              <Paperclip className="h-4 w-4" /> {tInbox("viewAttachment")}
            </a>
          )}
        </div>
        <Separator />
        {ticket.replies.map((reply) => (
          <ChatMessage
            key={reply.id}
            reply={reply}
            ticketCreatorId={ticket.user.id}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-2 border-t bg-background">
        <Tabs
          value={replyMode}
          onValueChange={(value) =>
            setReplyMode(value as "public" | "internal")
          }
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="public">
              <MessageSquare className="h-4 w-4 me-2" />
              {tInbox("publicReply")}
            </TabsTrigger>
            <TabsTrigger value="internal">
              <Lock className="h-4 w-4 me-2" />
              {tInbox("internalNote")}
            </TabsTrigger>
          </TabsList>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="relative mt-2"
            >
              <FormField
                control={form.control}
                name="message"
                render={({ field }) => (
                  <FormItem>
                    <FormControl>
                      <Textarea
                        placeholder={tInbox(
                          replyMode === "public"
                            ? "replyPlaceholder"
                            : "internalNotePlaceholder"
                        )}
                        className={cn(
                          "min-h-24 resize-none pe-12",
                          replyMode === "internal" &&
                            "bg-yellow-50/50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-800 focus-visible:ring-yellow-400"
                        )}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage className="absolute bottom-12 right-2 text-xs" />
                  </FormItem>
                )}
              />
              <Button
                type="submit"
                size="icon"
                className="absolute top-3 end-3"
                disabled={isReplying}
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </Form>
        </Tabs>
      </div>
    </div>
  );
}

function ChatMessage({
  reply,
  ticketCreatorId,
}: {
  reply: SupportTicketReply;
  ticketCreatorId: number;
}) {
  const isFromTicketCreator = reply.user.id === ticketCreatorId;

  if (reply.is_internal_note) {
    return (
      <div className="flex items-start gap-3 p-3 rounded-lg bg-yellow-100 dark:bg-yellow-900/50 border border-yellow-200 dark:border-yellow-800">
        <Lock className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-1" />
        <div>
          <p className="font-bold text-sm text-yellow-800 dark:text-yellow-300">
            ملاحظة داخلية من {reply.user.username}
          </p>
          <p className="text-sm whitespace-pre-wrap mt-1">{reply.message}</p>
          <p className="text-xs text-muted-foreground mt-2">
            {new Date(reply.created_at).toLocaleString(undefined, {
              dateStyle: "medium",
              timeStyle: "short",
            })}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex items-end gap-3 w-full",
        isFromTicketCreator && "justify-end"
      )}
    >
      {!isFromTicketCreator && (
        <Avatar className="h-8 w-8">
          <AvatarImage src={reply.user.profile_picture_url || ""} />
          <AvatarFallback>
            {reply.user.username.charAt(0).toUpperCase()}
          </AvatarFallback>
        </Avatar>
      )}
      <div
        className={cn(
          "max-w-xl p-3 rounded-lg flex flex-col",
          isFromTicketCreator
            ? "bg-primary text-primary-foreground items-end rounded-bl-none"
            : "bg-muted items-start rounded-br-none"
        )}
      >
        {!isFromTicketCreator && (
          <p className="font-semibold text-xs mb-1">
            {reply.user.preferred_name || reply.user.full_name}
          </p>
        )}
        <p className="text-sm whitespace-pre-wrap text-start">
          {reply.message}
        </p>
        <p
          className={cn(
            "text-xs mt-2",
            isFromTicketCreator ? "text-blue-200" : "text-muted-foreground"
          )}
        >
          {new Date(reply.created_at).toLocaleString(undefined, {
            timeStyle: "short",
          })}
        </p>
      </div>
      {isFromTicketCreator && (
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
