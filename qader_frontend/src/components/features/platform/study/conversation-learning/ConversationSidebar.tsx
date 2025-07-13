"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, MessageSquarePlus, SquarePen } from "lucide-react";
import * as z from "zod";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Image from "next/image";

import { useConversationStore } from "@/store/conversation.store";
import { startConversation } from "@/services/conversation.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
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
import { AITone } from "@/types/api/conversation.types";

const formSchema = z.object({
  ai_tone: z.enum(["cheerful", "serious"]),
});

type FormValues = z.infer<typeof formSchema>;

interface Props {
  isSending: boolean;
  onSendMessage: (message: string) => void;
  onAskForQuestion: () => void;
  onConfirmUnderstanding: () => void;
}
export const ConversationSidebar: React.FC<Props> = ({
  isSending,
  onSendMessage,
  onAskForQuestion,
  onConfirmUnderstanding,
}) => {
  const t = useTranslations("Study.conversationalLearning");
  const commonT = useTranslations("Common");
  const { resetConversation, sessionId, setSessionId, setMessages, setAiTone } =
    useConversationStore();

  const { control, handleSubmit } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { ai_tone: "cheerful" },
  });

  const startConversationMutation = useMutation({
    mutationFn: startConversation,
    onSuccess: (data) => {
      resetConversation();
      setSessionId(data.id);
      setMessages(data.messages.map((m) => ({ type: "text", content: m })));
      setAiTone(data.ai_tone);
      toast.success(t("api.startSuccess"));
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, t("api.startError")));
    },
  });

  const onStart = (values: FormValues) => {
    startConversationMutation.mutate({ ai_tone: values.ai_tone });
  };
  if (!sessionId) {
    return (
      <aside className="min-w-68 flex-col space-y-6 bg-card p-4 md:flex">
        <Card>
          <CardHeader>
            <CardTitle>{t("sidebarTitle")}</CardTitle>
            <CardDescription>{t("description")}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onStart)} className="space-y-4">
              <div>
                <Label htmlFor="ai-tone">{t("selectTone")}</Label>
                <Controller
                  name="ai_tone"
                  control={control}
                  render={({ field }) => (
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <SelectTrigger id="ai-tone" className="mt-1">
                        <SelectValue placeholder={t("selectTone")} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="cheerful">
                          {t("tone.cheerful")}
                        </SelectItem>
                        <SelectItem value="serious">
                          {t("tone.serious")}
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
              <Button
                type="submit"
                className="w-full"
                disabled={startConversationMutation.isPending}
              >
                {startConversationMutation.isPending ? (
                  <Loader2 className="me-2 h-4 w-4 animate-spin" />
                ) : (
                  <MessageSquarePlus className="me-2 h-4 w-4" />
                )}
                {startConversationMutation.isPending
                  ? commonT("loading")
                  : t("startConversation")}
              </Button>
            </form>
          </CardContent>
        </Card>
        {/* Future: Conversation History List could go here */}
      </aside>
    );
  }
  return (
    <div className="flex flex-nowrap min-w-[300px] md:flex-col mb-8 md:mb-0 overflow-x-auto md:overflow-x-hidden md:justify-end p-4 gap-4  max-w-full h-full md:max-w-[25%] md:w-1/4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
      <div className="flex flex-1 flex-col min-w-[268px] rounded-2xl dark:bg-[#0B1739] flex-shrink-0 items-center text-center justify-center gap-1 border p-4 h-full w-full hover:border-[#9EC9FA] hover:bg-[#9ec9fa3d] dark:hover:bg-[unset]">
        <Image
          src="/images/placeholder.svg"
          alt="Placeholder"
          width={268}
          height={300}
          className="object-contain md:w-full md:h-full mb-2 transition-all"
        />
        <p className="self-start font-semibold">{t("testMe")}</p>
        <p className="self-start text-muted-foreground">
          {t("testYourSkills")}
        </p>
        <Button
          className="w-full rounded-sm"
          onClick={onConfirmUnderstanding}
          disabled={isSending}
        >
          <SquarePen className="mr-2 h-4 w-4" />
          {t("testMe")}
        </Button>
      </div>

      <div className="flex flex-1 flex-col min-w-[268px] rounded-2xl items-center text-center justify-center gap-1 border p-4 h-full w-full dark:bg-[#0B1739] hover:border-[#9EC9FA] hover:bg-[#9ec9fa3d] dark:hover:bg-[unset]">
        <Image
          src="/images/placeholder.svg"
          alt="Placeholder"
          width={268}
          height={300}
          className="object-contain md:w-full md:h-full mb-2 transition-all"
        />
        <p className="self-start font-semibold">{t("askAQuestion")}</p>
        <p className="self-start text-muted-foreground">
          {t("askAQuestionHere")}
        </p>
        <Button
          className="w-full rounded-sm"
          onClick={onAskForQuestion}
          disabled={isSending}
        >
          <SquarePen className="mr-2 h-4 w-4" />
          {t("askAQuestion")}
        </Button>
      </div>
    </div>
  );
};
