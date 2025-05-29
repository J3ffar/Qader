"use client";

import React, { useEffect, useState, useRef, useMemo } from "react";
import Image from "next/image"; // Keep for potential non-Avatar images
import Link from "next/link"; // Use next's Link
import { useRouter } from "next/navigation"; // Use next's Router
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Loader2,
  AlertCircle,
  UploadCloud,
  User as UserIconLucide,
  Sparkles,
} from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

import {
  createCompleteProfileSchema,
  type CompleteProfileFormValues,
  type ApiCompleteProfileData,
} from "@/types/forms/auth.schema"; // Adjust path
import { completeUserProfile } from "@/services/auth.service"; // Adjust path
import { useAuthStore } from "@/store/auth.store"; // Adjust path
import { PATHS } from "@/constants/paths"; // Adjust path
import { QUERY_KEYS } from "@/constants/queryKeys"; // Adjust path

const grades = [
  "أولى ابتدائي",
  "ثانية ابتدائي",
  "ثالثة ابتدائي",
  "رابعة ابتدائي",
  "خامسة ابتدائي",
  "سادسة ابتدائي",
  "أولى متوسط",
  "ثانية متوسط",
  "ثالثة متوسط",
  "أولى ثانوي",
  "ثانية ثانوي",
  "ثالث ثانوي",
  "سنة تحضيرية جامعة",
  "طالب جامعي",
  "خريج",
  "أخرى",
]; // This list itself might need translation if you want it dynamic per locale

export default function CompleteProfilePage() {
  const tAuth = useTranslations("Auth");
  const tCommon = useTranslations("Common"); // For generic common terms if any
  const router = useRouter();
  const {
    accessToken,
    user,
    setUser: storeSetUser,
    isAuthenticated,
  } = useAuthStore();
  const [profilePreview, setProfilePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Memoize the schema creation
  const CurrentCompleteProfileSchema = useMemo(
    () => createCompleteProfileSchema(tAuth),
    [tAuth]
  );

  const {
    control,
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
    setError: setFormError,
  } = useForm<CompleteProfileFormValues>({
    resolver: zodResolver(CurrentCompleteProfileSchema),
    defaultValues: {
      gender: undefined,
      grade: "",
      has_taken_qiyas_before: undefined,
      preferred_name: user?.preferred_name || "",
      profile_picture: null,
      serial_code: "",
      referral_code_used: "",
      language: user?.language_code || "ar", // Default to user's current lang or 'ar'
    },
  });

  // Update defaultValues when user data is available
  useEffect(() => {
    if (user) {
      setValue("preferred_name", user.preferred_name || "");
      setValue("language", user.language_code || "ar");
      // If you store gender, grade, etc. in user object before profile completion, set them here too.
    }
  }, [user, setValue]);

  useEffect(() => {
    if (!isClient) return;
    if (!isAuthenticated || !accessToken) {
      toast.error(tAuth("loginRequired"));
      router.replace(PATHS.LOGIN); // PATHS.LOGIN should be non-localized base path
      return;
    }
    if (user?.profile_complete) {
      toast.info(tAuth("profileAlreadyComplete"));
      router.replace(PATHS.STUDY_HOME);
    }
  }, [isClient, isAuthenticated, accessToken, user, router, tAuth]);

  const completeProfileMutation = useMutation({
    mutationKey: [QUERY_KEYS.COMPLETE_PROFILE],
    mutationFn: (formDataValues: CompleteProfileFormValues) => {
      if (!accessToken) throw new Error(tAuth("accessTokenNotFound"));
      const apiData: ApiCompleteProfileData = {
        ...formDataValues,
        profile_picture: formDataValues.profile_picture?.[0] || null,
      };
      return completeUserProfile(apiData, accessToken);
    },
    onSuccess: (updatedUser) => {
      storeSetUser(updatedUser);
      toast.success(tAuth("profileUpdateSuccess"));
      router.push(PATHS.STUDY_HOME);
    },
    onError: (error: any) => {
      if (error.status === 400 && error.data) {
        Object.keys(error.data).forEach((key) => {
          const field = key as keyof CompleteProfileFormValues;
          const message = Array.isArray(error.data[key])
            ? error.data[key].join(", ")
            : String(error.data[key]);
          try {
            setFormError(field, { type: "server", message });
          } catch (e) {
            console.warn(`Could not set error for field: ${field}`);
          }
        });
        if (error.data.detail) {
          toast.error(String(error.data.detail));
        } else {
          let hasFieldErrors = false;
          Object.keys(createCompleteProfileSchema(tAuth).shape).forEach(
            (formKey) => {
              // Check against schema keys
              if (error.data[formKey]) hasFieldErrors = true;
            }
          );
          if (!hasFieldErrors) toast.error(tAuth("profileUpdateFailed"));
        }
      } else {
        toast.error(error.message || tAuth("serverError"));
      }
    },
  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      setValue("profile_picture", files as FileList, { shouldValidate: true });
      const reader = new FileReader();
      reader.onloadend = () => setProfilePreview(reader.result as string);
      reader.readAsDataURL(file);
    } else {
      setValue("profile_picture", null, { shouldValidate: true });
      setProfilePreview(null);
    }
  };

  const onSubmit = (data: CompleteProfileFormValues) =>
    completeProfileMutation.mutate(data);

  if (!isClient || (!isAuthenticated && !user)) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    );
  }
  if (user?.profile_complete) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="mt-4 text-muted-foreground">{tAuth("checkingProfile")}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto my-8 w-full max-w-xl space-y-6 rounded-xl border bg-card p-4 shadow-xl sm:p-6 md:p-8">
      <div className="text-center">
        <Sparkles className="mx-auto mb-3 h-12 w-12 text-primary" />
        <h1 className="text-3xl font-bold tracking-tight">
          {tAuth("completeProfilePageTitle")}
        </h1>
        <p className="mt-2 text-muted-foreground">
          {tAuth("completeProfilePageSubtitle")}
        </p>
      </div>

      {completeProfileMutation.isError &&
        !completeProfileMutation.error.data?.detail &&
        !Object.keys(createCompleteProfileSchema(tAuth).shape).some(
          (key) => (completeProfileMutation.error as any).data?.[key]
        ) && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>{tAuth("errorTitle")}</AlertTitle>
            <AlertDescription>
              {(completeProfileMutation.error as any)?.message ||
                tAuth("profileUpdateFailed")}
            </AlertDescription>
          </Alert>
        )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="flex flex-col items-center gap-3">
          <Label
            htmlFor="profile_picture_input_page"
            className="cursor-pointer"
          >
            {" "}
            {/* Unique ID */}
            <Avatar className="h-24 w-24 ring-2 ring-primary/50 ring-offset-2 ring-offset-background">
              <AvatarImage
                src={
                  profilePreview ||
                  user?.profile_picture_url ||
                  "/images/default-avatar.png"
                }
                alt={tAuth("profilePictureAlt")}
              />{" "}
              {/* Use a default avatar */}
              <AvatarFallback>
                <UserIconLucide className="h-12 w-12 text-muted-foreground" />
              </AvatarFallback>
            </Avatar>
          </Label>
          <input
            id="profile_picture_input_page"
            type="file"
            accept="image/*"
            className="hidden"
            {...register("profile_picture", { onChange: handleFileChange })}
            ref={fileInputRef}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            className="text-sm"
          >
            <UploadCloud className="mr-2 h-4 w-4 rtl:ml-2 rtl:mr-0" />
            {tAuth("uploadPicture")}
          </Button>
          {errors.profile_picture && (
            <p className="text-center text-xs text-red-500">
              {errors.profile_picture.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="gender_page" className="font-semibold">
            {tAuth("genderLabel")} <span className="text-destructive">*</span>
          </Label>{" "}
          {/* Unique ID */}
          <Controller
            name="gender"
            control={control}
            render={({ field }) => (
              <RadioGroup
                onValueChange={field.onChange}
                defaultValue={field.value}
                className="mt-2 flex space-x-4 rtl:space-x-reverse"
                dir={tCommon("dir") as "ltr" | "rtl"}
              >
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="male" id="male_page" />{" "}
                  <Label htmlFor="male_page">{tAuth("male")}</Label>
                </div>
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="female" id="female_page" />{" "}
                  <Label htmlFor="female_page">{tAuth("female")}</Label>
                </div>
              </RadioGroup>
            )}
          />
          {errors.gender && (
            <p className="mt-1 text-xs text-red-500">{errors.gender.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="preferred_name_page" className="font-semibold">
            {tAuth("preferredNameLabel")}
          </Label>{" "}
          {/* Unique ID */}
          <Input
            id="preferred_name_page"
            type="text"
            placeholder={tAuth("preferredNamePlaceholder")}
            {...register("preferred_name")}
            className="mt-1"
          />
          {errors.preferred_name && (
            <p className="mt-1 text-xs text-red-500">
              {errors.preferred_name.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="grade_page" className="font-semibold">
            {tAuth("gradeLabel")} <span className="text-destructive">*</span>
          </Label>{" "}
          {/* Unique ID */}
          <Controller
            name="grade"
            control={control}
            render={({ field }) => (
              <Select
                onValueChange={field.onChange}
                defaultValue={field.value}
                dir={tCommon("dir") as "ltr" | "rtl"}
              >
                <SelectTrigger className="mt-1 w-full">
                  <SelectValue placeholder={tAuth("selectGradePlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  {grades.map((gradeItem) => (
                    <SelectItem key={gradeItem} value={gradeItem}>
                      {gradeItem}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.grade && (
            <p className="mt-1 text-xs text-red-500">{errors.grade.message}</p>
          )}
        </div>

        <div>
          <Label className="font-semibold">
            {tAuth("hasTakenQiyasLabel")}{" "}
            <span className="text-destructive">*</span>
          </Label>
          <Controller
            name="has_taken_qiyas_before"
            control={control}
            render={({ field }) => (
              <RadioGroup
                onValueChange={(value) => field.onChange(value === "true")}
                defaultValue={
                  field.value === undefined ? undefined : String(field.value)
                }
                className="mt-2 flex space-x-4 rtl:space-x-reverse"
                dir={tCommon("dir") as "ltr" | "rtl"}
              >
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="true" id="qiyas_yes_page" />{" "}
                  <Label htmlFor="qiyas_yes_page">{tAuth("yes")}</Label>
                </div>
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="false" id="qiyas_no_page" />{" "}
                  <Label htmlFor="qiyas_no_page">{tAuth("no")}</Label>
                </div>
              </RadioGroup>
            )}
          />
          {errors.has_taken_qiyas_before && (
            <p className="mt-1 text-xs text-red-500">
              {errors.has_taken_qiyas_before.message}
            </p>
          )}
        </div>

        {/* Language: This should ideally be set from user's preference or locale,
            and might not need to be a user-editable field here if it's already determined.
            If it's just for API submission, the hidden input is fine.
            Ensure `user?.language_code` is correctly populated.
        */}
        <input type="hidden" {...register("language")} />
        {errors.language && (
          <p className="mt-1 text-xs text-red-500">{errors.language.message}</p>
        )}

        <div>
          <Label htmlFor="serial_code_page" className="font-semibold">
            {tAuth("serialCodeLabel")}
          </Label>{" "}
          {/* Unique ID */}
          <Input
            id="serial_code_page"
            type="text"
            placeholder={tAuth("serialCodePlaceholder")}
            {...register("serial_code")}
            className="mt-1"
          />
          {errors.serial_code && (
            <p className="mt-1 text-xs text-red-500">
              {errors.serial_code.message}
            </p>
          )}
          <p className="mt-1 text-xs text-muted-foreground">
            {tAuth("serialCodeHint")}
          </p>
        </div>

        <div>
          <Label htmlFor="referral_code_used_page" className="font-semibold">
            {tAuth("referralCodeLabel")}
          </Label>{" "}
          {/* Unique ID */}
          <Input
            id="referral_code_used_page"
            type="text"
            placeholder={tAuth("referralCodePlaceholder")}
            {...register("referral_code_used")}
            className="mt-1"
          />
          {errors.referral_code_used && (
            <p className="mt-1 text-xs text-red-500">
              {errors.referral_code_used.message}
            </p>
          )}
          <p className="mt-1 text-xs text-muted-foreground">
            {tAuth("referralCodeHint")}
          </p>
        </div>

        <div className="pt-4">
          <Button
            type="submit"
            className="w-full py-3 text-base sm:py-6 sm:text-lg"
            disabled={completeProfileMutation.isPending}
          >
            {completeProfileMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin rtl:ml-2 rtl:mr-0" />
                {tAuth("savingButton")}
              </>
            ) : (
              tAuth("completeSignupButton")
            )}
          </Button>
          <Button variant="link" asChild className="mt-2 w-full">
            <Link href={PATHS.HOME}>{tAuth("backToHomeLater")}</Link>
          </Button>
        </div>
      </form>
    </div>
  );
}
