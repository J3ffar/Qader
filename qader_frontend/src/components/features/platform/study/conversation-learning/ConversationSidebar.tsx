"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { SparklesIcon } from "@heroicons/react/24/solid";

import { useConversationStore } from "@/store/conversation.store";
import {
  AITone,
  StartConversationPayload,
} from "@/types/api/conversation.types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";

interface ConversationSidebarProps {
  onStartConversation: (payload: StartConversationPayload) => void;
  isStarting: boolean;
}

export function ConversationSidebar({
  onStartConversation,
  isStarting,
}: ConversationSidebarProps) {
  const t = useTranslations("Study.conversationalLearning");
  const { aiTone, setAiTone } = useConversationStore();

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault();
    onStartConversation({ ai_tone: aiTone });
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{t("sidebarTitle")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleStart} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="ai-tone">{t("selectTone")}</Label>
            <Select
              value={aiTone}
              onValueChange={(value) => setAiTone(value as AITone)}
              disabled={isStarting}
            >
              <SelectTrigger id="ai-tone">
                <SelectValue placeholder={t("selectTone")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="cheerful">{t("tone.cheerful")}</SelectItem>
                <SelectItem value="serious">{t("tone.serious")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button type="submit" className="w-full" disabled={isStarting}>
            {isStarting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin rtl:ml-2" />
            ) : (
              <SparklesIcon className="mr-2 h-4 w-4 rtl:ml-2" />
            )}
            {t("startConversation")}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
