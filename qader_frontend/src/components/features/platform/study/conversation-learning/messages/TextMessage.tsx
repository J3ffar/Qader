import React from "react";
import { Bot, User } from "lucide-react";
import { ConversationMessage } from "@/types/api/conversation.types";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import logo from "../../../../../../../public/images/logoside.png"
import Image from "next/image";

export const TextMessage = ({ message }: { message: ConversationMessage }) => {
  const isUser = message.sender_type === "user";
  return (
    <div
      className={cn(
        "flex items-start gap-4",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <Avatar className="h-9 w-9">
          <AvatarFallback>
                      <Image src={logo} width={36} height={36} alt="" className=" rounded-full object-contain" />

          </AvatarFallback>
        </Avatar>
      )}
      <div
        className={cn(
          "max-w-xl rounded-lg px-4 py-2",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted"
        )}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{message.message_text}</ReactMarkdown>
        </div>
      </div>
      {isUser && (
        <Avatar className="h-9 w-9">
          <AvatarFallback>
            <User />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
};
