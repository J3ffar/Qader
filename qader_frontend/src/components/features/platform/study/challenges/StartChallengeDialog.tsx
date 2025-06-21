"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { createChallenge } from "@/services/challenges.service";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { ChallengeType } from "@/types/api/challenges.types";

// Runtime object for ChallengeType to be used with Zod's nativeEnum
const ChallengeTypeEnum = {
  quick_quant_10: "quick_quant_10",
  medium_verbal_15: "medium_verbal_15",
  comprehensive_20: "comprehensive_20",
  speed_challenge_5min: "speed_challenge_5min",
  accuracy_challenge: "accuracy_challenge",
  custom: "custom",
} as const; // 'as const' ensures it's a readonly object with literal types

interface StartChallengeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const formSchema = z.object({
  opponent_username: z.string().optional(),
  challenge_type: z.nativeEnum(ChallengeTypeEnum, {
    required_error: "Please select a challenge type.",
  }),
});

export function StartChallengeDialog({
  open,
  onOpenChange,
}: StartChallengeDialogProps) {
  const t = useTranslations("Study.challenges");
  const queryClient = useQueryClient();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      opponent_username: "",
      challenge_type: ChallengeTypeEnum.quick_quant_10, // Default value
    },
  });

  const createChallengeMutation = useMutation({
    mutationFn: createChallenge,
    onSuccess: () => {
      toast.success(t("challengeSentSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.challenges.lists() as unknown as string[],
      });
      onOpenChange(false);
      form.reset();
    },
    onError: (error) => {
      const errorMessage = getApiErrorMessage(error);
      if (errorMessage.includes("User not found")) {
        // Basic check, improve with specific API error codes
        toast.error(t("errorUserNotFound"));
      } else {
        toast.error(t("errorGeneric"));
      }
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    createChallengeMutation.mutate({
      opponent_username: (values.opponent_username as string) || null, // Explicitly cast to string | null
      challenge_type: values.challenge_type,
    });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t("createChallengeTitle")}</DialogTitle>
          <DialogDescription>{t("description")}</DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="opponent_username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("opponentUsername")}</FormLabel>
                  <FormControl>
                    <Input
                      placeholder={t("opponentUsernamePlaceholder")}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="challenge_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("challengeType")}</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder={t("challengeType")} />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {/* TODO: Replace with dynamic challenge types from API if available */}
                      <SelectItem value="quick_quant_10">
                        Quick Quant (10 Qs)
                      </SelectItem>
                      <SelectItem value="medium_verbal_15">
                        Medium Verbal (15 Qs)
                      </SelectItem>
                      <SelectItem value="comprehensive_20">
                        Comprehensive (20 Qs)
                      </SelectItem>
                      <SelectItem value="speed_challenge_5min">
                        Speed Challenge (5 min)
                      </SelectItem>
                      <SelectItem value="accuracy_challenge">
                        Accuracy Challenge
                      </SelectItem>
                      <SelectItem value="custom">Custom</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="submit"
                disabled={createChallengeMutation.isPending}
              >
                {createChallengeMutation.isPending
                  ? "Sending..."
                  : t("startChallenge")}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
