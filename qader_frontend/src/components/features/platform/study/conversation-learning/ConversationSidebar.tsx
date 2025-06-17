"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, MessageSquarePlus } from "lucide-react";
import * as z from "zod";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

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

export const ConversationSidebar = () => {
  const t = useTranslations("Study.conversationalLearning");
  const commonT = useTranslations("Common");
  const { resetConversation, setSessionId, setMessages, setAiTone } =
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

  return (
    <aside className="hidden w-80 flex-col space-y-6 border-e bg-card p-4 md:flex">
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
};
