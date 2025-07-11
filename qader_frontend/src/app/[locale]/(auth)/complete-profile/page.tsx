"use client";

import React, { useEffect, useState, useRef, useMemo } from "react";
// Image from next/image is good if you have static images, otherwise Avatar is fine.
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Loader2,
  AlertCircle,
  UploadCloud,
  User as UserIconLucide,
  Sparkles,
  CheckCircle, // For success indication
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
import { Skeleton } from "@/components/ui/skeleton"; // For loading state

import {
  createCompleteProfileSchema,
  type CompleteProfileFormValues,
  type ApiCompleteProfileData,
} from "@/types/forms/auth.schema";
import { getGrades, completeUserProfile } from "@/services/auth.service";
import { useAuthCore, useAuthActions, useAuthStore } from "@/store/auth.store"; // Added useAuthCore
import { PATHS } from "@/constants/paths";
import type { ApiError, UserProfile, Grade } from "@/types/api/auth.types";
import { queryKeys } from "@/constants/queryKeys";

export default function CompleteProfilePage() {
  const tAuth = useTranslations("Auth");
  const tCommon = useTranslations("Common");
  const router = useRouter();

  // Use custom hooks for state and actions
  const { user, isAuthenticated, accessToken, isProfileComplete } =
    useAuthCore();
  const {
    setUser: storeSetUser,
    setIsProfileComplete: storeSetIsProfileComplete,
  } = useAuthActions();

  const {
    data: grades = [],
    isLoading: isLoadingGrades,
    error: gradesError,
  } = useQuery({
    queryKey: queryKeys.user.grades(),
    queryFn: getGrades,
    staleTime: 1000 * 60 * 60, // Grades list is static, cache for 1 hour
    refetchOnWindowFocus: false,
  });

  const [profilePreview, setProfilePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isClientHydrated, setIsClientHydrated] = useState(false); // Renamed for clarity

  useEffect(() => {
    setIsClientHydrated(true);
  }, []);

  const CurrentCompleteProfileSchema = useMemo(
    () => createCompleteProfileSchema(tAuth), // Assuming tAuth has all necessary keys
    [tAuth]
  );

  const {
    control,
    register,
    handleSubmit,
    watch, // Keep if you use it for dynamic UI based on form values
    setValue,
    formState: { errors, isSubmitting }, // isSubmitting can be useful
    setError: setFormError,
    reset, // For resetting form after successful submission if needed
  } = useForm<CompleteProfileFormValues>({
    resolver: zodResolver(CurrentCompleteProfileSchema),
    // Default values will be set/updated by useEffect below
  });

  // Initialize form with user data or defaults
  useEffect(() => {
    if (user) {
      reset({
        // Use reset to update all defaultValues at once
        gender: user.gender || undefined,
        grade: user.grade || "",
        has_taken_qiyas_before:
          user.has_taken_qiyas_before === null
            ? undefined
            : user.has_taken_qiyas_before,
        preferred_name: user.preferred_name || "",
        serial_code: "", // Usually not pre-filled unless editing
        referral_code_used: "", // Usually not pre-filled
        username: user.username || "", // Add username if it's part of the form
      });
      if (user.profile_picture_url) {
        setProfilePreview(user.profile_picture_url);
      }
    } else {
      // Default values if no user (though redirect should prevent this state)
      reset({
        gender: undefined,
        grade: "",
        has_taken_qiyas_before: undefined,
        preferred_name: "",
        serial_code: "",
        referral_code_used: "",
        language: "ar",
        username: "",
      });
    }
  }, [user, reset]); // reset is stable

  // Auth and profile completion checks
  useEffect(() => {
    if (!isClientHydrated) return; // Wait for client hydration

    if (!isAuthenticated || !accessToken) {
      toast.error(tAuth("loginRequired"));
      router.replace(PATHS.LOGIN);
      return;
    }
    if (isProfileComplete) {
      // Use isProfileComplete from store
      // toast.info(tAuth("profileAlreadyComplete"));
      router.replace(PATHS.STUDY.HOME);
    }
  }, [
    isClientHydrated,
    isAuthenticated,
    accessToken,
    isProfileComplete,
    router,
    tAuth,
  ]);

  const completeProfileMutation = useMutation<
    UserProfile, // Expected success response type
    ApiError, // Error type
    CompleteProfileFormValues // Variables type
  >({
    mutationKey: queryKeys.user.completeProfile(),
    mutationFn: (formDataValues: CompleteProfileFormValues) => {
      // accessToken is already checked by the useEffect above or available from useAuth()
      if (!useAuthStore.getState().accessToken)
        throw new Error(tAuth("accessTokenNotFound"));

      // Transform form data to API data
      const apiData: ApiCompleteProfileData = {
        gender: formDataValues.gender!, // Should be guaranteed by schema
        grade: formDataValues.grade!, // Should be guaranteed by schema
        has_taken_qiyas_before: formDataValues.has_taken_qiyas_before!, // Should be guaranteed
        language: formDataValues.language || "ar", // Default if somehow empty
        preferred_name: formDataValues.preferred_name || null,
        profile_picture: formDataValues.profile_picture_filelist?.[0] || null, // Use filelist field
        serial_code: formDataValues.serial_code || null,
        referral_code_used: formDataValues.referral_code_used || null,
        username: formDataValues.username || null,
      };
      // The service function `completeUserProfile` should not require accessToken as a param
      // if apiClient handles it. The refactored service in previous step does this.
      return completeUserProfile(apiData);
    },
    onSuccess: (updatedUser) => {
      storeSetUser(updatedUser); // This updates the user in the store
      storeSetIsProfileComplete(updatedUser.profile_complete); // Explicitly set profile completion
      toast.success(tAuth("profileUpdateSuccess"));
      router.push(PATHS.STUDY.HOME);
    },
    onError: (error: ApiError) => {
      if (error.status === 400 && error.data) {
        let hasFieldErrors = false;
        Object.keys(error.data).forEach((key) => {
          // Ensure key is a valid form field before setting error
          if (key in CurrentCompleteProfileSchema.shape) {
            const field = key as keyof CompleteProfileFormValues;
            const message = Array.isArray(error.data![key])
              ? (error.data![key] as string[]).join(", ")
              : String(error.data![key]);
            setFormError(field, { type: "server", message });
            hasFieldErrors = true;
          }
        });

        if (error.data.detail) {
          toast.error(String(error.data.detail));
        } else if (!hasFieldErrors) {
          // Only show generic if no field errors and no detail
          toast.error(tAuth("profileUpdateFailed"));
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
      // Use the correct field name from Zod schema for FileList
      setValue("profile_picture_filelist", files, { shouldValidate: true });
      const reader = new FileReader();
      reader.onloadend = () => setProfilePreview(reader.result as string);
      reader.readAsDataURL(file);
    } else {
      setValue("profile_picture_filelist", null, { shouldValidate: true });
      setProfilePreview(user?.profile_picture_url || null); // Revert to original if cleared
    }
  };

  const onSubmit = (data: CompleteProfileFormValues) => {
    completeProfileMutation.mutate(data);
  };

  // Loading state while checking auth or if user data is not yet loaded
  if (
    !isClientHydrated ||
    (!isAuthenticated && !user && !completeProfileMutation.isError)
  ) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6">
        {/* Skeleton for the form card */}
        <div className="w-full max-w-xl space-y-6 rounded-xl border bg-card p-8 shadow-xl">
          <div className="mb-6 text-center">
            <Skeleton className="mx-auto mb-3 h-12 w-12 rounded-full" />
            <Skeleton className="mx-auto mb-2 h-8 w-3/4" />
            <Skeleton className="mx-auto h-4 w-1/2" />
          </div>
          <div className="space-y-6">
            <Skeleton className="mx-auto mb-2 h-24 w-24 rounded-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="mt-4 h-12 w-full" />
          </div>
        </div>
      </div>
    );
  }

  // This state means user.profile_complete was true initially, redirecting...
  if (isClientHydrated && isProfileComplete) {
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

      {/* Non-field specific error display */}
      {completeProfileMutation.isError &&
        completeProfileMutation.error.data?.detail && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>{tAuth("errorTitle")}</AlertTitle>
            <AlertDescription>
              {String(completeProfileMutation.error.data.detail)}
            </AlertDescription>
          </Alert>
        )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Profile Picture */}
        <div className="flex flex-col items-center gap-3">
          <Label
            htmlFor="profile_picture_input_page"
            className="cursor-pointer"
          >
            <Avatar className="h-24 w-24 ring-2 ring-primary/50 ring-offset-2 ring-offset-background">
              <AvatarImage
                src={profilePreview || "/images/default-avatar.png"} // API sends full URL
                alt={tAuth("profilePictureAlt")}
              />
              <AvatarFallback>
                <UserIconLucide className="h-12 w-12 text-muted-foreground" />
              </AvatarFallback>
            </Avatar>
          </Label>
          <input
            id="profile_picture_input_page" // Unique ID
            type="file"
            accept="image/*"
            className="hidden"
            // Use Controller for file inputs for better integration with RHF validation
            // Or use `register` but ensure `profile_picture_filelist` matches Zod schema
            {...register("profile_picture_filelist")} // Changed to profile_picture_filelist
            onChange={handleFileChange} // Keep custom onChange if needed
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
          {errors.profile_picture_filelist && ( // Check errors for profile_picture_filelist
            <p className="text-center text-xs text-red-500">
              {errors.profile_picture_filelist.message}
            </p>
          )}
        </div>

        {/* Username (Optional based on your schema) */}
        <div>
          <Label htmlFor="username_page" className="font-semibold">
            {tAuth("usernameLabel")}
          </Label>
          <Input
            id="username_page"
            type="text"
            placeholder={tAuth("usernamePlaceholder")}
            {...register("username")}
            className="mt-1"
            aria-invalid={errors.username ? "true" : "false"}
          />
          {errors.username && (
            <p className="mt-1 text-xs text-red-500">
              {errors.username.message}
            </p>
          )}
        </div>

        {/* Gender */}
        <div>
          <Label htmlFor="gender_page_male" className="font-semibold">
            {" "}
            {/* Point to first option */}
            {tAuth("genderLabel")} <span className="text-destructive">*</span>
          </Label>
          <Controller
            name="gender"
            control={control}
            render={({ field }) => (
              <RadioGroup
                onValueChange={field.onChange}
                value={field.value} // Use value for controlled component
                className="mt-2 flex space-x-4 rtl:space-x-reverse"
                dir={tCommon("dir") as "ltr" | "rtl"}
              >
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="male" id="gender_page_male" />{" "}
                  {/* Unique ID */}
                  <Label htmlFor="gender_page_male">{tAuth("male")}</Label>
                </div>
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="female" id="gender_page_female" />{" "}
                  {/* Unique ID */}
                  <Label htmlFor="gender_page_female">{tAuth("female")}</Label>
                </div>
                {/* Add "other" and "prefer_not_to_say" if your schema supports them */}
              </RadioGroup>
            )}
          />
          {errors.gender && (
            <p className="mt-1 text-xs text-red-500">{errors.gender.message}</p>
          )}
        </div>

        {/* Preferred Name */}
        <div>
          <Label htmlFor="preferred_name_page" className="font-semibold">
            {tAuth("preferredNameLabel")}
          </Label>
          <Input
            id="preferred_name_page" // Unique ID
            type="text"
            placeholder={tAuth("preferredNamePlaceholder")}
            {...register("preferred_name")}
            className="mt-1"
            aria-invalid={errors.preferred_name ? "true" : "false"}
          />
          {errors.preferred_name && (
            <p className="mt-1 text-xs text-red-500">
              {errors.preferred_name.message}
            </p>
          )}
        </div>

        {/* Grade */}
        <div>
          <Label htmlFor="grade_page_trigger" className="font-semibold">
            {" "}
            {/* Point to trigger */}
            {tAuth("gradeLabel")} <span className="text-destructive">*</span>
          </Label>
          <Controller
            name="grade"
            control={control}
            render={({ field }) => (
              <Select
                onValueChange={field.onChange}
                value={field.value} // Use value for controlled
                dir={tCommon("dir") as "ltr" | "rtl"}
                disabled={isLoadingGrades}
              >
                <SelectTrigger id="grade_page_trigger" className="mt-1 w-full">
                  {" "}
                  {/* Unique ID */}
                  <SelectValue placeholder={tAuth("selectGradePlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  {grades.map((grade) => (
                    <SelectItem key={grade.key} value={grade.key}>
                      {grade.label}
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

        {/* Has Taken Qiyas Before */}
        <div>
          <Label className="font-semibold" htmlFor="qiyas_yes_page">
            {" "}
            {/* Point to first option */}
            {tAuth("hasTakenQiyasLabel")}{" "}
            <span className="text-destructive">*</span>
          </Label>
          <Controller
            name="has_taken_qiyas_before"
            control={control}
            render={({ field }) => (
              <RadioGroup
                onValueChange={(value) => field.onChange(value === "true")}
                value={
                  field.value === undefined ? undefined : String(field.value)
                } // Use value
                className="mt-2 flex space-x-4 rtl:space-x-reverse"
                dir={tCommon("dir") as "ltr" | "rtl"}
              >
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="true" id="qiyas_yes_page" />{" "}
                  {/* Unique ID */}
                  <Label htmlFor="qiyas_yes_page">{tCommon("yes")}</Label>
                </div>
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="false" id="qiyas_no_page" />{" "}
                  {/* Unique ID */}
                  <Label htmlFor="qiyas_no_page">{tCommon("no")}</Label>
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

        {/* Language - if it's always based on user's settings or current locale, can be hidden */}
        {/* If user can CHOOSE language for their profile separate from UI, use a Select */}
        <input type="hidden" {...register("language")} defaultValue="ar" />

        {errors.language && (
          <p className="mt-1 text-xs text-red-500">{errors.language.message}</p>
        )}

        {/* Serial Code */}
        <div>
          <Label htmlFor="serial_code_page" className="font-semibold">
            {tAuth("serialCodeLabel")}
          </Label>
          <Input
            id="serial_code_page" // Unique ID
            type="text"
            placeholder={tAuth("serialCodePlaceholder")}
            {...register("serial_code")}
            className="mt-1"
            aria-invalid={errors.serial_code ? "true" : "false"}
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

        {/* Referral Code */}
        <div>
          <Label htmlFor="referral_code_used_page" className="font-semibold">
            {tAuth("referralCodeLabel")}
          </Label>
          <Input
            id="referral_code_used_page" // Unique ID
            type="text"
            placeholder={tAuth("referralCodePlaceholder")}
            {...register("referral_code_used")}
            className="mt-1"
            aria-invalid={errors.referral_code_used ? "true" : "false"}
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
            className="w-full py-3 text-base sm:py-3 sm:text-lg" // Adjusted padding for sm
            disabled={completeProfileMutation.isPending || isSubmitting}
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
