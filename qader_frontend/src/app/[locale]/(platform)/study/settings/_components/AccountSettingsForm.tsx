"use client";

import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { useAuthStore } from "@/store/auth.store";
import { updateUserProfile } from "@/services/auth.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { User, Edit3 } from "lucide-react";
import { useRef, useState } from "react";
import { UserProfile } from "@/types/api/auth.types";
import ChangePasswordDialog from "./ChangePasswordDialog";
import { queryKeys } from "@/constants/queryKeys";
import { useParams } from "next/navigation";
import { cn } from "@/lib/utils";

// Schema for form validation
const accountSettingsSchema = z.object({
  full_name: z.string().min(3, "Full name must be at least 3 characters."),
  preferred_name: z.string().optional(),
  profile_picture: z.instanceof(File).optional(),
});

type AccountSettingsValues = z.infer<typeof accountSettingsSchema>;

interface AccountSettingsFormProps {
  user: UserProfile;
}

export default function AccountSettingsForm({
  user,
}: AccountSettingsFormProps) {
  const t = useTranslations("Study.settings.account");
  const queryClient = useQueryClient();
  const { updateUserProfile: updateUserInStore } = useAuthStore();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(
    user.profile_picture_url
  );
  const { locale } = useParams();
  const form = useForm<AccountSettingsValues>({
    resolver: zodResolver(accountSettingsSchema),
    defaultValues: {
      full_name: user.full_name || "",
      preferred_name: user.preferred_name || "",
    },
  });

  const mutation = useMutation({
    mutationFn: (data: FormData) => updateUserProfile(data),
    onSuccess: (updatedUser) => {
      toast.success(t("toast.success"));
      updateUserInStore(updatedUser);
      queryClient.invalidateQueries({
        queryKey: queryKeys.user.profile(user.id),
      });
    },
    onError: (error) => {
      toast.error(t("toast.error"), {
        description: getApiErrorMessage(error, t("toast.error")),
      });
    },
  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      form.setValue("profile_picture", file, { shouldDirty: true });
      setPreview(URL.createObjectURL(file));
    }
  };

  function onSubmit(data: AccountSettingsValues) {
    const formData = new FormData();
    formData.append("full_name", data.full_name);
    if (data.preferred_name) {
      formData.append("preferred_name", data.preferred_name);
    }
    if (data.profile_picture) {
      formData.append("profile_picture", data.profile_picture);
    }
    mutation.mutate(formData);
  }

  return (
    <Card className="w-full max-w-6xl mx-auto mt-8 dark:bg-[#0B1739] border-2 dark:border-[#7E89AC]">
      <CardHeader>
        <CardTitle className={cn( locale === "ar" ? "text-right" : "text-left")}>{t("title")}</CardTitle>
        <CardDescription className={cn( locale === "ar" ? "text-right" : "text-left")}>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            <div dir={locale==="ar"?"ltr":"rtl"} className="flex flex-row gap-4 items-center">
              <div className="flex-1">
                <p className={cn( "text-lg font-semibold",locale === "ar" ? "text-right" : "text-left")} >{t("upload.title")}</p>
                <p className={cn( "text-muted-foreground",locale === "ar" ? "text-right" : "text-left")} >{t("upload.title")} 
                  {t("upload.description")}
                </p>
              </div>
              <div className="relative">
                <Avatar className="h-24 w-24">
                  <AvatarImage
                    src={preview || ""}
                    alt={user.preferred_name || user.full_name}
                  />
                  <AvatarFallback>
                    <User className="h-12 w-12" />
                  </AvatarFallback>
                </Avatar>
                <Button
                  type="button"
                  size="icon"
                  className="absolute bottom-0 end-0 rounded-full cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Edit3 className="h-4 w-4" />
                </Button>
                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  accept="image/png, image/jpeg, image/webp"
                  onChange={handleFileChange}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <FormField
                control={form.control}
                name="full_name"
                render={({ field }) => (
                  <FormItem  dir={locale === "ar" ? "rtl" : "ltr"}>
                    <FormLabel >{t("fullName.label")}</FormLabel>
                    <FormControl >
                      <Input
                        placeholder={t("fullName.placeholder")}
                        {...field}
                        className={cn( "text-lg",locale === "ar" ? "text-right" : "text-left")} 
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="preferred_name"
                render={({ field }) => (
                  <FormItem dir={locale === "ar" ? "rtl" : "ltr"}>
                    <FormLabel>{t("preferredName.label")}</FormLabel>
                    <FormControl>
                      <Input
                        placeholder={t("preferredName.placeholder")}
                        {...field}
                        className={cn(locale === "ar" ? "text-right" : "text-left")}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormItem dir={locale === "ar" ? "rtl" : "ltr"} className='cursor-not-allowed' >
                <FormLabel>{t("email.label")}</FormLabel>
                <FormControl>
                  <Input className={cn(locale === "ar" ? "text-right" : "text-left")} value={user.email} disabled />
                </FormControl>
              </FormItem>

              <FormItem dir={locale === "ar" ? "rtl" : "ltr"}>
                <FormLabel className={cn(locale === "ar" ? "text-right" : "text-left")}>{t("password.label")}</FormLabel>
                <ChangePasswordDialog />
              </FormItem>
            </div>

            <div dir={locale === "en" ? "rtl" : "ltr"} className="flex justify-start">
              <Button
                type="submit"
                disabled={!form.formState.isDirty || mutation.isPending}
              >
                {mutation.isPending ? t("buttons.saving") : t("buttons.save")}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
