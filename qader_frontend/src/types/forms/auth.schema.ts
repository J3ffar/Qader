import { z } from "zod";
import type { AppMessages } from "@/types/i18n"; // Use the central AppMessages type

// Derives the keys specifically from the 'Auth' namespace within AppMessages
type AuthNamespaceKeys = keyof AppMessages["Auth"];

/**
 * Defines the expected signature for the `t` function when specialized for the 'Auth' namespace.
 * This `t` function is typically obtained from `useTranslations('Auth')` in a component.
 * For Zod error messages, this function must produce a string.
 */
export type AuthTFunction = (
  key: AuthNamespaceKeys,
  /** Values for interpolation in the translation string. */
  values?: Record<string, string | number> // For Zod, values usually resolve to simple types.
  // next-intl's t can accept ReactNode for rich text,
  // but Zod messages need to be strings.
) => string;

// --- Login Schema ---
export const createLoginSchema = (t: AuthTFunction) =>
  z.object({
    username: z
      .string()
      .min(1, {
        message: t("requiredField", { fieldName: t("emailOrUsername") }),
      })
      .refine(
        (value) =>
          z.string().email().safeParse(value).success ||
          /^[a-zA-Z0-9_.-]+$/.test(value),
        {
          message: t("usernameOrEmailInvalid"),
        }
      ),
    password: z
      .string()
      .min(1, { message: t("requiredField", { fieldName: t("password") }) }),
    rememberMe: z.boolean().optional(),
  });
export type LoginCredentials = z.infer<ReturnType<typeof createLoginSchema>>;

// --- Signup Schema---
export const createSignupSchema = (t: AuthTFunction) =>
  z
    .object({
      full_name: z
        .string()
        .min(3, { message: t("fullNameMinLength") })
        .max(100, { message: t("fullNameMaxLength") })
        .regex(/^[ \p{L}\p{M}'-]+$/u, { message: t("fullNameInvalidChars") }),
      email: z
        .string()
        .min(1, { message: t("requiredField", { fieldName: t("email") }) })
        .email({ message: t("emailInvalid") }),
      password: z
        .string()
        .min(8, { message: t("passwordMinLength") })
        .max(128, { message: t("passwordMaxLength") })
        .regex(
          /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&._-])[A-Za-z\d@$!%*?&._-]+$/,
          { message: t("passwordComplexity") }
        ),
      password_confirm: z.string().min(1, {
        message: t("requiredField", { fieldName: t("confirmPassword") }),
      }),
      termsAccepted: z.boolean().refine((val) => val === true, {
        message: t("termsRequired"),
      }),
    })
    .refine((data) => data.password === data.password_confirm, {
      message: t("passwordsMismatch"),
      path: ["password_confirm"],
    });
export type SignupFormValues = z.infer<ReturnType<typeof createSignupSchema>>;
// API data for signup: full_name, email, password, password_confirm
export type ApiSignupData = Omit<
  SignupFormValues,
  "termsAccepted" | "password_confirm"
> & {
  password_confirm: string; // Ensure it's sent if backend expects it for validation, otherwise omit
};
// Based on API docs for POST /auth/signup/: email, full_name, password, password_confirm
// So the current ApiSignupData is nearly correct, just ensure password_confirm is included.

// --- Helper for profile picture validation (remains the same) ---
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ACCEPTED_IMAGE_TYPES = [
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
];

// --- Complete Profile Schema ---
// Based on API docs for PATCH /users/me/complete-profile/
// Required: gender, grade, has_taken_qiyas_before
// Optional: username, language, preferred_name, profile_picture, serial_code, referral_code_used
export const createCompleteProfileSchema = (t: AuthTFunction) =>
  z.object({
    // Optional fields that can be set during profile completion
    username: z
      .string()
      .min(3, { message: t("usernameMinLength", { min: 3 }) })
      .max(50, { message: t("usernameMaxLength", { max: 50 }) })
      .regex(/^[a-zA-Z0-9_.-]+$/, { message: t("usernameInvalidFormat") })
      .optional()
      .nullable(),
    preferred_name: z
      .string()
      .max(100, { message: t("preferredNameMaxLength") })
      .optional()
      .nullable(),
    profile_picture_filelist: z // Keep FileList for form handling
      .custom<FileList>()
      .refine(
        (files) =>
          !files || files.length === 0 || files?.[0]?.size <= MAX_FILE_SIZE,
        t("profilePictureSizeLimit")
      )
      .refine(
        (files) =>
          !files ||
          files.length === 0 ||
          (files?.[0]?.type && ACCEPTED_IMAGE_TYPES.includes(files[0].type)),
        t("profilePictureInvalidFormat")
      )
      .optional()
      .nullable(),
    serial_code: z
      .string()
      .max(50, { message: t("serialCodeMaxLength") })
      .optional()
      .nullable(),
    referral_code_used: z
      .string()
      .max(50, { message: t("referralCodeMaxLength") })
      .optional()
      .nullable(),
    language: z
      .enum(["ar", "en"], {
        // Ensure these values match your `locales` array in i18n.config.ts
        // This field is optional in API, but if provided, must be valid
        errorMap: (issue, ctx) => ({ message: t("languageInvalid") }),
      })
      .optional(),

    // Required fields for the API
    gender: z.enum(["male", "female"], {
      // Match API choices
      required_error: t("genderRequired"),
      invalid_type_error: t("genderInvalid"),
    }),
    grade: z
      .string()
      .min(1, { message: t("gradeRequired") })
      .max(50, { message: t("gradeMaxLength") }), // Define max length if any
    has_taken_qiyas_before: z.boolean({
      required_error: t("qiyasTakenRequired"),
      invalid_type_error: t("qiyasTakenInvalid"),
    }),
  });

export type CompleteProfileFormValues = z.infer<
  ReturnType<typeof createCompleteProfileSchema>
>;

// Data structure for the API call (multipart/form-data if profile_picture is included)
export type ApiCompleteProfileData = {
  username?: string | null;
  gender: "male" | "female" | "other" | "prefer_not_to_say";
  grade: string;
  has_taken_qiyas_before: boolean;
  language?: "ar" | "en" | string;
  preferred_name?: string | null;
  profile_picture?: File | null; // Single File for API
  serial_code?: string | null;
  referral_code_used?: string | null;
};

// --- Request OTP Schema ---
export const createRequestOtpSchema = (t: AuthTFunction) =>
  z.object({
    identifier: z
      .string()
      .min(1, { message: t("identifierRequired") })
      .refine(
        (value) =>
          z.string().email().safeParse(value).success ||
          /^[a-zA-Z0-9_.-]+$/.test(value),
        {
          message: t("identifierInvalid"),
        }
      ),
  });
export type RequestOtpFormValues = z.infer<
  ReturnType<typeof createRequestOtpSchema>
>;

// --- Verify OTP Schema ---
export const createVerifyOtpSchema = (t: AuthTFunction) =>
  z.object({
    identifier: z.string(), // Usually pre-filled from previous step
    otp: z
      .string()
      .min(6, { message: t("otpMinLength") })
      .max(6, { message: t("otpMaxLength") })
      .regex(/^\d{6}$/, { message: t("otpInvalidFormat") }),
  });
export type VerifyOtpFormValues = z.infer<
  ReturnType<typeof createVerifyOtpSchema>
>;

// --- Reset Password Schema ---
// API endpoint: /auth/password/reset/confirm-otp/
// API body: reset_token, new_password, new_password_confirm
export const createResetPasswordSchema = (t: AuthTFunction) =>
  z
    .object({
      reset_token: z.string(), // This will come from verifyOtp response
      new_password: z
        .string()
        .min(8, { message: t("newPasswordMinLength") })
        .regex(
          /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&._-])[A-Za-z\d@$!%*?&._-]+$/,
          { message: t("passwordComplexity") }
        ),
      new_password_confirm: z
        .string()
        .min(1, { message: t("newPasswordConfirmRequired") }),
    })
    .refine((data) => data.new_password === data.new_password_confirm, {
      message: t("newPasswordsMismatch"),
      path: ["new_password_confirm"],
    });
export type ResetPasswordFormValues = z.infer<
  ReturnType<typeof createResetPasswordSchema>
>;

// New schema for the change password dialog
export const createChangePasswordSchema = (t: AuthTFunction) =>
  z
    .object({
      current_password: z
        .string()
        .min(1, {
          message: t("requiredField", { fieldName: t("currentPassword") }),
        }),
      new_password: z
        .string()
        .min(8, { message: t("passwordMinLength") })
        .regex(
          /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&._-])[A-Za-z\d@$!%*?&._-]+$/,
          { message: t("passwordComplexity") }
        ),
      new_password_confirm: z.string(),
    })
    .refine((data) => data.new_password === data.new_password_confirm, {
      message: t("passwordsMismatch"),
      path: ["new_password_confirm"],
    });

export type ChangePasswordFormValues = z.infer<
  ReturnType<typeof createChangePasswordSchema>
>;
