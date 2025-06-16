"use client";

import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";
import { Loader2 } from "lucide-react";

import * as convoService from "@/services/conversation.service";
import { useConversationStore } from "@/store/conversation.store";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function ChatInputBar() {
  const t = useTranslations("Study.conversationalLearning");
  const {
    sessionId,
    isSending,
    addMessage,
    setIsSending,
    setActiveTestQuestion,
    activeTestQuestion,
  } = useConversationStore();

  const [messageText, setMessageText] = useState("");

  const commonMutationOptions = {
    onMutate: () => setIsSending(true),
    onSettled: () => setIsSending(false),
    onError: (error: unknown) => {
      toast.error(t("api.sendMessageError"), {
        description: getApiErrorMessage(error, t("api.sendMessageError")),
      });
    },
  };

  const sendMessageMutation = useMutation({
    ...commonMutationOptions,
    mutationKey: [QUERY_KEYS.CONVERSATION_SEND_MESSAGE],
    mutationFn: (payload: { sessionId: number; text: string }) =>
      convoService.sendMessage(payload.sessionId, {
        message_text: payload.text,
      }),
    onSuccess: (data) => addMessage({ type: "text", content: data }),
  });

  const askQuestionMutation = useMutation({
    ...commonMutationOptions,
    mutationKey: [QUERY_KEYS.CONVERSATION_ASK_QUESTION],
    mutationFn: (payload: { sessionId: number }) =>
      convoService.askForQuestion(payload.sessionId),
    onSuccess: (data) => {
      addMessage({ type: "question", content: data, sender: "ai" });
      setActiveTestQuestion(data.question);
    },
  });

  const confirmUnderstandingMutation = useMutation({
    ...commonMutationOptions,
    mutationKey: [QUERY_KEYS.CONVERSATION_CONFIRM_UNDERSTANDING],
    mutationFn: (payload: { sessionId: number }) =>
      convoService.confirmUnderstanding(payload.sessionId),
    onSuccess: (data) => {
      // UPDATED: Handle new response structure and 204 No Content
      if (data && data.test_question) {
        // AI returned a test question
        addMessage({
          type: "question",
          content: {
            ai_message: data.ai_message,
            question: data.test_question,
          },
          sender: "ai",
        });
        setActiveTestQuestion(data.test_question); // <-- RENAMED
      } else {
        // Handle 204 No Content or response without a question
        toast.info("رائع! لننتقل إلى الموضوع التالي. ما الذي ترغب بمناقشته؟");
      }
    },
  });

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageText.trim() || !sessionId) return;

    // Add user message to UI immediately for better UX
    addMessage({
      type: "text",
      content: {
        id: Date.now(), // Temporary ID for key prop
        sender_type: "user",
        message_text: messageText,
        related_question_id: null,
        timestamp: new Date().toISOString(),
      },
    });

    sendMessageMutation.mutate({ sessionId, text: messageText });
    setMessageText("");
  };

  // If there's an active test question, the user must answer it first.
  if (activeTestQuestion) {
    return (
      <div className="animate-pulse border-t p-4 text-center text-muted-foreground">
        الرجاء الإجابة على السؤال أعلاه للاستمرار.
      </div>
    );
  }

  return (
    <div className="border-t bg-background p-4">
      <div className="flex flex-col gap-2">
        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            onClick={() =>
              sessionId && askQuestionMutation.mutate({ sessionId })
            }
            disabled={!sessionId || isSending}
          >
            {askQuestionMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {t("askAQuestion")}
          </Button>
          <Button
            onClick={() =>
              sessionId && confirmUnderstandingMutation.mutate({ sessionId })
            }
            disabled={!sessionId || isSending}
          >
            {confirmUnderstandingMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {t("testMyUnderstanding")}
          </Button>
        </div>
        <form
          onSubmit={handleSendMessage}
          className="flex w-full items-center space-x-2 rtl:space-x-reverse"
        >
          <Input
            type="text"
            value={messageText}
            onChange={(e) => setMessageText(e.target.value)}
            placeholder={t("inputPlaceholder")}
            disabled={!sessionId || isSending}
            autoComplete="off"
          />
          <Button type="submit" disabled={!sessionId || isSending}>
            {t("send")}
            <PaperAirplaneIcon className="ml-2 h-4 w-4 rtl:mr-2" />
          </Button>
        </form>
      </div>
    </div>
  );
}
