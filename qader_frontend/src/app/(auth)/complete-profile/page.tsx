"use client";

import React, { useEffect, useState, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Loader2,
  AlertCircle,
  CheckCircle2,
  UploadCloud,
  User as UserIconLucide,
  Sparkles,
} from "lucide-react"; // Using Lucide

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
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"; // For Yes/No
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import {
  CompleteProfileSchema,
  type CompleteProfileFormValues,
  type ApiCompleteProfileData,
} from "@/types/forms/auth.schema";
import { completeUserProfile } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth.store";
import { PATHS } from "@/constants/paths";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { QUERY_KEYS } from "@/constants/queryKeys";
// import { useTranslations } from 'next-intl';

const grades = [
  // You can move this to a constants file or fetch from API if dynamic
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
];

export default function CompleteProfilePage() {
  // const t = useTranslations('Auth.CompleteProfile');
  // const tCommon = useTranslations('Common');
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
    setIsClient(true); // Set to true once component has mounted on the client
  }, []);

  const {
    control,
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
    setError: setFormError,
  } = useForm<CompleteProfileFormValues>({
    resolver: zodResolver(CompleteProfileSchema),
    defaultValues: {
      gender: undefined, // Let placeholder show
      grade: "",
      has_taken_qiyas_before: undefined, // Let placeholder show or default to false
      preferred_name: user?.preferred_name || "",
      profile_picture: null,
      serial_code: "",
      referral_code_used: "",
      language: "ar", // Default to Arabic or get from user profile if available
    },
  });

  // Redirect if not authenticated or profile already complete
  useEffect(() => {
    if (!isClient) return;

    if (!isAuthenticated || !accessToken) {
      toast.error("الرجاء تسجيل الدخول أولاً للمتابعة."); // t('loginRequired')
      router.replace(PATHS.HOME || "/"); // Redirect to login if not authenticated
      return;
    }
    if (user?.profile_complete) {
      toast.info("ملفك الشخصي مكتمل بالفعل."); // t('profileAlreadyComplete')
      router.replace(PATHS.STUDY_HOME || "/study"); // Redirect if profile is already complete
    }
  }, [isClient, isAuthenticated, accessToken, user, router]);

  const completeProfileMutation = useMutation({
    mutationKey: QUERY_KEYS.COMPLETE_PROFILE,
    mutationFn: (formDataValues: CompleteProfileFormValues) => {
      if (!accessToken) {
        throw new Error("Access token not found."); // Should be caught by useEffect ideally
      }
      // Transform form data for the API
      const apiData: ApiCompleteProfileData = {
        ...formDataValues,
        profile_picture: formDataValues.profile_picture?.[0] || null, // Get the File object
      };
      return completeUserProfile(apiData, accessToken);
    },
    onSuccess: (updatedUser) => {
      storeSetUser(updatedUser); // Update user in Zustand store
      toast.success("تم تحديث ملفك الشخصي بنجاح!"); // t('profileUpdateSuccess')
      // The API response contains the updated user profile.
      // It also indicates if a trial was activated or serial code applied.
      // The backend should handle subscription activation messages via notifications if needed.
      router.push(PATHS.STUDY_HOME || "/study"); // Navigate to study page
    },
    onError: (error: any) => {
      if (error.status === 400 && error.data) {
        Object.keys(error.data).forEach((key) => {
          const field = key as keyof CompleteProfileFormValues;
          const message = Array.isArray(error.data[key])
            ? error.data[key].join(", ")
            : error.data[key];
          try {
            setFormError(field, { type: "server", message });
          } catch (e) {
            console.warn(`Could not set error for field: ${field}`);
          }
        });
        if (error.data.detail) {
          toast.error(error.data.detail);
        } else {
          toast.error(
            "فشل تحديث الملف الشخصي. الرجاء التحقق من البيانات المدخلة."
          ); // t('profileUpdateFailed')
        }
      } else {
        toast.error(error.message || "فشل الاتصال بالخادم. حاول لاحقاً."); // t('serverError')
      }
    },
  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      setValue("profile_picture", files as FileList, { shouldValidate: true }); // Update RHF state
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfilePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    } else {
      setValue("profile_picture", null, { shouldValidate: true });
      setProfilePreview(null);
    }
  };

  const onSubmit = (data: CompleteProfileFormValues) => {
    completeProfileMutation.mutate(data);
  };

  // Loading state for page if user data is not yet available from store
  if (!isClient || (!isAuthenticated && !user)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background p-6">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
      </div>
    );
  }
  // If user is loaded but profile is complete, useEffect will redirect. Show loading until then.
  if (user?.profile_complete) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background p-6">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
        <p className="mt-4 text-muted-foreground">
          جاري التحقق من الملف الشخصي...
        </p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-xl mx-auto p-4 sm:p-6 md:p-8 space-y-6 bg-card shadow-xl rounded-xl border">
      <div className="text-center">
        <Sparkles className="mx-auto h-12 w-12 text-primary mb-3" />
        <h1 className="text-3xl font-bold tracking-tight">
          أكمل ملفك الشخصي
        </h1>{" "}
        {/* t('pageTitle') */}
        <p className="text-muted-foreground mt-2">
          {/* t('pageSubtitle') */}الرجاء إدخال التفاصيل المتبقية لبدء رحلتك
          التعليمية.
        </p>
      </div>

      {completeProfileMutation.isError &&
        !completeProfileMutation.error.data?.detail && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>خطأ</AlertTitle>
            <AlertDescription>
              {(completeProfileMutation.error as any)?.message ||
                "فشل تحديث الملف الشخصي. الرجاء التحقق من البيانات المدخلة."}
            </AlertDescription>
          </Alert>
        )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Profile Picture Upload */}
        <div className="flex flex-col items-center gap-3">
          <Label htmlFor="profile_picture_input" className="cursor-pointer">
            <Avatar className="h-24 w-24 ring-2 ring-primary/50 ring-offset-2 ring-offset-background">
              <AvatarImage
                src={
                  profilePreview ||
                  user?.profile_picture_url ||
                  "/images/signup.png"
                }
                alt="Profile Preview"
              />
              <AvatarFallback>
                <UserIconLucide className="h-12 w-12 text-muted-foreground" />
              </AvatarFallback>
            </Avatar>
          </Label>
          <input
            id="profile_picture_input"
            type="file"
            accept="image/*"
            className="hidden"
            {...register("profile_picture", { onChange: handleFileChange })} // RHF handles the FileList
            ref={fileInputRef}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            className="text-sm"
          >
            <UploadCloud className="mr-2 h-4 w-4" />
            {/* t('uploadPicture') */}تغيير الصورة
          </Button>
          {errors.profile_picture && (
            <p className="text-xs text-red-500 text-center">
              {errors.profile_picture.message}
            </p>
          )}
        </div>

        {/* Gender */}
        <div>
          <Label htmlFor="gender" className="font-semibold">
            الجنس <span className="text-destructive">*</span>
          </Label>{" "}
          {/* t('gender') */}
          <Controller
            name="gender"
            control={control}
            render={({ field }) => (
              <RadioGroup
                onValueChange={field.onChange}
                defaultValue={field.value}
                className="flex space-x-4 rtl:space-x-reverse mt-2"
                dir="rtl" // For RTL layout of radio items
              >
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="male" id="male" />
                  <Label htmlFor="male">ذكر</Label>
                  {/* t('male') */}
                </div>
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="female" id="female" />
                  <Label htmlFor="female">أنثى</Label>
                  {/* t('female') */}
                </div>
              </RadioGroup>
            )}
          />
          {errors.gender && (
            <p className="mt-1 text-xs text-red-500">{errors.gender.message}</p>
          )}
        </div>

        {/* Preferred Name */}
        <div>
          <Label htmlFor="preferred_name" className="font-semibold">
            الاسم المفضل (اختياري)
          </Label>
          {/* t('preferredName') */}
          <Input
            id="preferred_name"
            type="text"
            placeholder="سالم" //{t('preferredNamePlaceholder')}
            {...register("preferred_name")}
            className="mt-1"
          />
          {errors.preferred_name && (
            <p className="mt-1 text-xs text-red-500">
              {errors.preferred_name.message}
            </p>
          )}
        </div>

        {/* Grade */}
        <div>
          <Label htmlFor="grade" className="font-semibold">
            الصف الدراسي <span className="text-destructive">*</span>
          </Label>
          {/* t('grade') */}
          <Controller
            name="grade"
            control={control}
            render={({ field }) => (
              <Select
                onValueChange={field.onChange}
                defaultValue={field.value}
                dir="rtl"
              >
                <SelectTrigger className="w-full mt-1">
                  <SelectValue placeholder="اختر الصف الدراسي" />
                  {/* t('selectGradePlaceholder') */}
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

        {/* Has Taken Qiyas Before */}
        <div>
          <Label className="font-semibold">
            هل اختبرت قدرات من قبل؟ <span className="text-destructive">*</span>
          </Label>
          {/* t('hasTakenQiyas') */}
          <Controller
            name="has_taken_qiyas_before"
            control={control}
            render={({ field }) => (
              <RadioGroup
                onValueChange={(value) => field.onChange(value === "true")} // Convert string "true"/"false" to boolean
                defaultValue={
                  field.value === undefined ? undefined : String(field.value)
                }
                className="flex space-x-4 rtl:space-x-reverse mt-2"
                dir="rtl"
              >
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="true" id="qiyas_yes" />
                  <Label htmlFor="qiyas_yes">نعم</Label>
                  {/* t('yes') */}
                </div>
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <RadioGroupItem value="false" id="qiyas_no" />
                  <Label htmlFor="qiyas_no">لا</Label>
                  {/* t('no') */}
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

        {/* Language (hidden but required by API) */}
        <input type="hidden" {...register("language")} defaultValue="ar" />
        {/* Or make it a visible select if users should choose
         <div>
          <Label htmlFor="language">Language</Label>
          <Controller name="language" control={control} render={({ field }) => (
            <Select onValueChange={field.onChange} defaultValue={field.value || "ar"}>
              <SelectTrigger><SelectValue placeholder="Select language" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ar">العربية</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
          )} />
          {errors.language && <p className="text-xs text-red-500">{errors.language.message}</p>}
        </div>
        */}

        {/* Serial Code */}
        <div>
          <Label htmlFor="serial_code" className="font-semibold">
            الرمز التسلسلي (اختياري)
          </Label>
          {/* t('serialCode') */}
          <Input
            id="serial_code"
            type="text"
            placeholder="QADER-ABC123" //{t('serialCodePlaceholder')}
            {...register("serial_code")}
            className="mt-1"
          />
          {errors.serial_code && (
            <p className="mt-1 text-xs text-red-500">
              {errors.serial_code.message}
            </p>
          )}
          <p className="mt-1 text-xs text-muted-foreground">
            {/* t('serialCodeHint') */}إذا كان لديك رمز تسلسلي للاشتراك، أدخله
            هنا. وفي حال لم تدخل رمز تسلسلي, تستطيع تجربة المنصة ليوم واحد مع
            بعض القيود.
          </p>
        </div>

        {/* Referral Code */}
        <div>
          <Label htmlFor="referral_code_used" className="font-semibold">
            رمز الإحالة (اختياري)
          </Label>
          {/* t('referralCode') */}
          <Input
            id="referral_code_used"
            type="text"
            placeholder="REF-XYZ789" //{t('referralCodePlaceholder')}
            {...register("referral_code_used")}
            className="mt-1"
          />
          {errors.referral_code_used && (
            <p className="mt-1 text-xs text-red-500">
              {errors.referral_code_used.message}
            </p>
          )}
          <p className="mt-1 text-xs text-muted-foreground">
            {/* t('referralCodeHint') */}إذا دعاك صديق، أدخل رمز الإحالة الخاص
            به هنا.
          </p>
        </div>

        <div className="pt-4">
          <Button
            type="submit"
            className="w-full text-lg py-6"
            disabled={completeProfileMutation.isPending}
          >
            {completeProfileMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                {/* t('savingButton') */}جارٍ الحفظ...
              </>
            ) : (
              //t('completeSignupButton')
              "إكمال التسجيل وحفظ البيانات"
            )}
          </Button>
          <Button variant="link" asChild className="w-full mt-2">
            <Link href={PATHS.HOME || "/"}>العودة إلى الرئيسية لاحقًا</Link>
          </Button>
        </div>
      </form>
    </div>
  );
}
