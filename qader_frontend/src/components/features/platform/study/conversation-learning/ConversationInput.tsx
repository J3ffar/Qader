"use client";

import React, { useState, useMemo } from "react";
import { useTranslations } from "next-intl";
import { Bot, Lightbulb, Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Props {
  isSending: boolean;
  onSendMessage: (message: string) => void;
  onAskForQuestion: () => void;
  onConfirmUnderstanding: () => void;
}

export const ConversationInput: React.FC<Props> = ({
  isSending,
  onSendMessage,
  onAskForQuestion,
  onConfirmUnderstanding,
}) => {
  const t = useTranslations("Study.conversationalLearning");
  const [message, setMessage] = useState("");
  const MAX_WORDS = 40;

  // Count words in the message
  const wordCount = useMemo(() => {
    return message.trim() === "" ? 0 : message.trim().split(/\s+/).length;
  }, [message]);

  // Check if word limit is exceeded
  const isOverLimit = wordCount > MAX_WORDS;
  const isNearLimit = wordCount > MAX_WORDS * 0.8; // 80% of limit (32 words)

  const handleSend = () => {
    if (message.trim() && !isOverLimit) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 w-full min-w-[300px]">
      <div className="mx-auto max-w-3xl">
        <div className="relative dark:bg-[#091029] rounded-xl">
          <Textarea
            placeholder={t("inputPlaceholder")}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSending}
            rows={1}
            className={`min-h-[48px] resize-none dark:bg-[#091029] rounded-xl p-4 pe-16 ${
              isOverLimit ? "border-red-500 dark:border-red-400" : ""
            }`}
          />
          <Button
            type="submit"
            size="icon"
            className="absolute end-3 top-1/2 -translate-y-1/2 rounded-sm w-fit px-4 cursor-pointer"
            onClick={handleSend}
            disabled={isSending || !message.trim() || isOverLimit}
          >
            <Send className="h-5 w-5" />
            <span>{t("send")}</span>
          </Button>
        </div>
        
        {/* Word count indicator */}
        <div className="flex justify-end mt-2 px-1">
          <span
            className={`text-sm ${
              isOverLimit
                ? "text-red-500 dark:text-red-400"
                : isNearLimit
                ? "text-yellow-500 dark:text-yellow-400"
                : "text-gray-500 dark:text-gray-400"
            }`}
          >
            {wordCount}/{MAX_WORDS} words
          </span>
        </div>
        
        {/* Warning message when over limit */}
        {isOverLimit && (
          <div className="mt-1 px-1">
            <span className="text-sm text-red-500 dark:text-red-400">
              Message exceeds {MAX_WORDS} word limit. Please shorten your message.
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
