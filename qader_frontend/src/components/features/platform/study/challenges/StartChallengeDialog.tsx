"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Loader2, Check } from "lucide-react";
import Image from "next/image";

import five from "../../../../../../public/images/grp1.png";
import two from "../../../../../../public/images/grp2.png";
import one from "../../../../../../public/images/grp3.png";
import four from "../../../../../../public/images/grp6.png";
import three from "../../../../../../public/images/grp5.png";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import {
  createChallenge,
  getChallengeTypes,
  markAsReady,
} from "@/services/challenges.service";
import { queryKeys } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { CreateChallengePayload } from "@/types/api/challenges.types";

interface StartChallengeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Map images to challenge types (you may need to adjust the keys based on your actual challenge types)
const challengeTypeImages = [
  { key: "accuracy", image: one, label: "تحدي الدقة", description: "من يحقق أعلى نسبة دقة" },
  { key: "focus", image: two, label: "لفظي متوسط", description: "15 سؤال بدون تلميحات" },
  { key: "speed", image: three, label: "كمي سريع", description: "10 أسئلة بوقت سريع" },
  { key: "speed_challenge", image: four, label: "تحدي السرعة", description: "من يحل أكثر خلال 5 دقائق" },
  { key: "comprehensive", image: five, label: "تحدي شامل", description: "20 سؤال من أقسام مختلفة" },
];

export function StartChallengeDialog({
  open,
  onOpenChange,
}: StartChallengeDialogProps) {
  const t = useTranslations("Study.challenges");
  const tCommon = useTranslations("Common");
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);

  const challengeFormSchema = z.object({
    opponent_username: z.string().optional(),
    challenge_type: z.string({
      required_error: t("errorGeneric"),
    }),
  });

  const form = useForm<z.infer<typeof challengeFormSchema>>({
    resolver: zodResolver(challengeFormSchema),
    defaultValues: {
      opponent_username: "",
      challenge_type: "",
    },
  });

  const { data: challengeTypes, isLoading: isLoadingTypes } = useQuery({
    queryKey: queryKeys.challenges.types(),
    queryFn: getChallengeTypes,
  });

  const createChallengeMutation = useMutation({
    mutationFn: createChallenge,
    onSuccess: async (newChallenge) => {
      toast.promise(markAsReady(newChallenge.id), {
        loading: t("creatingAndPreparing"),
        success: () => {
          queryClient.invalidateQueries({
            queryKey: queryKeys.challenges.lists(),
          });
          router.push(`${PATHS.STUDY.CHALLENGE_COLLEAGUES}/${newChallenge.id}`);
          setIsOpen(false);
          form.reset();
          return t("challengeSentAndReady");
        },
        error: (err) => getApiErrorMessage(err, t("errorGeneric")),
      });
    },
    onError: (error) => {
      const message = getApiErrorMessage(error, t("errorGeneric"));
      if (message.toLowerCase().includes("user not found")) {
        form.setError("opponent_username", {
          type: "manual",
          message: t("errorUserNotFound"),
        });
      } else {
        toast.error(message);
      }
    },
  });

  function onSubmit(values: z.infer<typeof challengeFormSchema>) {
    const payload: CreateChallengePayload = {
      opponent_username: values.opponent_username || "",
      challenge_type: values.challenge_type,
    };
    createChallengeMutation.mutate(payload);
  }

  // Get the actual challenge types from the API and map them to images
  const getMappedChallengeTypes = () => {
    if (!challengeTypes) return challengeTypeImages;
    
    return challengeTypes.map((type, index) => ({
      key: type.key,
      image: challengeTypeImages[index]?.image || one,
      label: type.name,
      description: type.description,
    }));
  };

  const mappedTypes = getMappedChallengeTypes();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="text-center text-xl">
            {t("createChallengeTitle")}
          </DialogTitle>
          <DialogDescription className="text-center">
            {t("createChallengeDescription")}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
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
                      className="text-right"
                      dir="rtl"
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
                  <FormControl>
                    <div className="grid grid-cols-5 gap-3 mt-4">
                      {isLoadingTypes ? (
                        <div className="col-span-5 flex justify-center py-8">
                          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                        </div>
                      ) : (
                        mappedTypes.map((type) => (
                          <button
                            key={type.key}
                            type="button"
                            onClick={() => field.onChange(type.key)}
                            className={cn(
                              "relative flex flex-col items-center p-3 rounded-lg transition-all duration-200",
                              "hover:bg-gray-50 hover:shadow-md",
                              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
                              field.value === type.key
                                ? "bg-blue-50 ring-2 ring-blue-500 shadow-md"
                                : "bg-white border border-gray-200"
                            )}
                          >
                            {field.value === type.key && (
                              <div className="absolute -top-2 -right-2 bg-blue-500 rounded-full p-1">
                                <Check className="h-3 w-3 text-white" />
                              </div>
                            )}
                            
                            <div className="w-16 h-16 mb-2 relative">
                              <Image
                                src={type.image}
                                alt={type.label}
                                fill
                                className="object-contain"
                              />
                            </div>
                            
                            <h4 className="text-xs font-semibold text-gray-900 text-center mb-1">
                              {type.label}
                            </h4>
                            
                            <p className="text-[10px] text-gray-500 text-center leading-tight">
                              {type.description}
                            </p>
                          </button>
                        ))
                      )}
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <DialogFooter>
              <Button
                type="submit"
                disabled={createChallengeMutation.isPending || !form.watch("challenge_type")}
                className="w-full sm:w-auto"
              >
                {createChallengeMutation.isPending && (
                  <Loader2 className="ltr:mr-2 rtl:ml-2 h-4 w-4 animate-spin" />
                )}
                {t("startChallenge")}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
