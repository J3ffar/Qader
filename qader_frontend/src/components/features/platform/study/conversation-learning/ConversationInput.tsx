"use client";

import React, { useState } from "react";
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

  const handleSend = () => {
    if (message.trim()) {
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
    <div className="border-t bg-background p-4">
      <div className="mx-auto max-w-3xl">
        <div className="mb-2 flex justify-center space-x-2 rtl:space-x-reverse">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onAskForQuestion}
                  disabled={isSending}
                >
                  <Bot className="me-2 h-4 w-4" /> {t("askAQuestion")}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{t("askAQuestion")}</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onConfirmUnderstanding}
                  disabled={isSending}
                >
                  <Lightbulb className="me-2 h-4 w-4" />{" "}
                  {t("testMyUnderstanding")}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{t("testMyUnderstanding")}</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <div className="relative">
          <Textarea
            placeholder={t("inputPlaceholder")}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSending}
            rows={1}
            className="min-h-[48px] resize-none rounded-2xl p-4 pe-16"
          />
          <Button
            type="submit"
            size="icon"
            className="absolute end-3 top-1/2 -translate-y-1/2 rounded-full"
            onClick={handleSend}
            disabled={isSending || !message.trim()}
          >
            <Send className="h-5 w-5" />
            <span className="sr-only">{t("send")}</span>
          </Button>
        </div>
      </div>
    </div>
  );
};
