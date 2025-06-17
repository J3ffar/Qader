"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { BotMessageSquare } from "lucide-react";

import { useConversationStore } from "@/store/conversation.store";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import {
  sendMessage,
  askForQuestion,
  confirmUnderstanding,
} from "@/services/conversation.service";

import { ConversationSidebar } from "./ConversationSidebar";
import { ConversationInput } from "./ConversationInput";
import { MessageList } from "./MessageList";

export const ConversationLearningClient = () => {
  const t = useTranslations("Study.conversationalLearning");
  const {
    sessionId,
    addMessage,
    isSending,
    setIsSending,
    setActiveTestQuestion,
  } = useConversationStore();

  const mutationOptions = {
    onMutate: () => setIsSending(true),
    onError: (error: Error) => {
      toast.error(getApiErrorMessage(error, t("api.sendMessageError")));
    },
    onSettled: () => setIsSending(false),
  };

  const sendMessageMutation = useMutation({
    ...mutationOptions,
    mutationFn: (messageText: string) => {
      if (!sessionId) throw new Error("Session ID is missing");
      return sendMessage(sessionId, { message_text: messageText });
    },
    onSuccess: (aiResponse) => {
      addMessage({ type: "text", content: aiResponse });
    },
  });

  const askQuestionMutation = useMutation({
    ...mutationOptions,
    mutationFn: () => {
      if (!sessionId) throw new Error("Session ID is missing");
      return askForQuestion(sessionId);
    },
    onSuccess: (data) => {
      // API now sends a question inside a message wrapper
      addMessage({ type: "question", content: data, sender: "ai" });
    },
  });

  const confirmUnderstandingMutation = useMutation({
    ...mutationOptions,
    mutationFn: () => {
      if (!sessionId) throw new Error("Session ID is missing");
      return confirmUnderstanding(sessionId);
    },
    onSuccess: (data) => {
      if (data && "ai_message" in data) {
        // Check if API returned a test question
        // This now becomes a special "question" type message
        addMessage({
          type: "question",
          content: {
            ai_message: data.ai_message,
            question: data.test_question,
          },
          sender: "ai",
        });
      }
      // If the response is empty (204 No Content), do nothing.
    },
  });

  const handleSendMessage = (message: string) => {
    // Optimistically add user message
    const userMessage = {
      id: Date.now(),
      sender_type: "user" as const,
      message_text: message,
      related_question_id: null,
      timestamp: new Date().toISOString(),
    };
    addMessage({ type: "text", content: userMessage });
    sendMessageMutation.mutate(message);
  };

  if (!sessionId) {
    return (
      <div className="flex h-[calc(100vh-8rem)]">
        <ConversationSidebar />
        <div className="flex flex-1 flex-col items-center justify-center text-center">
          <BotMessageSquare className="h-16 w-16 text-muted-foreground" />
          <h2 className="mt-4 text-2xl font-semibold">
            {t("emptyStateTitle")}
          </h2>
          <p className="mt-2 text-muted-foreground">
            {t("emptyStateDescription")}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-8rem)]">
      <ConversationSidebar />
      <div className="flex flex-1 flex-col">
        <MessageList />
        <ConversationInput
          isSending={isSending}
          onSendMessage={handleSendMessage}
          onAskForQuestion={() => askQuestionMutation.mutate()}
          onConfirmUnderstanding={() => confirmUnderstandingMutation.mutate()}
        />
      </div>
    </div>
  );
};
