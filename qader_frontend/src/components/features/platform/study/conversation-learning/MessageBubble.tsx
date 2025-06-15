"use client";

import React from "react";
import { motion } from "framer-motion";
import { Bot, User } from "lucide-react";

import { cn } from "@/lib/utils";
import { CustomMessageType } from "@/types/api/conversation.types";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { QuestionCard } from "./QuestionCard";

interface MessageBubbleProps {
  message: CustomMessageType;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser =
    message.type === "text" && message.content.sender_type === "user";
  const renderContent = () => {
    switch (message.type) {
      case "text":
        return <p className="text-sm">{message.content.message_text}</p>;
      case "question":
        return (
          <QuestionCard question={message.content.question} isTestMode={true} />
        );
      case "feedback":
        return (
          <>
            <p className="mb-4 text-sm font-semibold">
              {message.content.ai_feedback}
            </p>
            <QuestionCard
              question={message.content.question}
              isTestMode={false}
              testResult={message.content}
            />
          </>
        );
      default:
        return null;
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className={cn("flex items-start gap-3", isUser && "justify-end")}
    >
      {!isUser && (
        <Avatar className="h-8 w-8">
          <AvatarImage src="/images/logo/qader-icon.svg" alt="AI" />
          <AvatarFallback>
            <Bot />
          </AvatarFallback>
        </Avatar>
      )}

      <div
        className={cn(
          "max-w-xl rounded-lg p-3",
          isUser
            ? "bg-primary text-primary-foreground rounded-br-none rtl:rounded-bl-none rtl:rounded-br-lg"
            : "bg-muted rounded-bl-none rtl:rounded-br-none rtl:rounded-bl-lg"
        )}
      >
        {renderContent()}
      </div>

      {isUser && (
        <Avatar className="h-8 w-8">
          {/* We would get user image from auth store */}
          <AvatarImage src="" alt="User" />
          <AvatarFallback>
            <User />
          </AvatarFallback>
        </Avatar>
      )}
    </motion.div>
  );
}
