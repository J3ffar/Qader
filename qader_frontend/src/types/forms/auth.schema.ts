import { z } from "zod";

import type { AppMessages } from "@/types/i18n"; // Import the central AppMessages type

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
) => string; // Zod error messages must be strings.

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

// --- Signup Schema ---
export const SignupSchema = (t: AuthTFunction) =>
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
export type SignupFormValues = z.infer<ReturnType<typeof SignupSchema>>;
export type ApiSignupData = Omit<SignupFormValues, "termsAccepted">;

// --- Helper for profile picture validation (remains the same) ---
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ACCEPTED_IMAGE_TYPES = [
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
];

// --- Complete Profile Schema ---
export const createCompleteProfileSchema = (t: AuthTFunction) =>
  z.object({
    gender: z.enum(["male", "female"], {
      required_error: t("genderRequired"),
      invalid_type_error: t("genderInvalid"),
    }),
    grade: z
      .string()
      .min(1, { message: t("gradeRequired") })
      .max(50, { message: t("gradeMaxLength") }),
    has_taken_qiyas_before: z.boolean({
      required_error: t("qiyasTakenRequired"),
      invalid_type_error: t("qiyasTakenInvalid"),
    }),
    preferred_name: z
      .string()
      .max(100, { message: t("preferredNameMaxLength") })
      .optional()
      .nullable(),
    profile_picture: z
      .custom<FileList>()
      .refine(
        (files) =>
          files === undefined ||
          files === null ||
          files.length === 0 ||
          files?.[0]?.size <= MAX_FILE_SIZE,
        t("profilePictureSizeLimit")
      )
      .refine(
        (files) =>
          files === undefined ||
          files === null ||
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
    language: z.enum(["ar", "en"], {
      // Ensure these values match your `locales` array in i18n.ts
      required_error: t("languageRequired"),
    }),
  });
export type CompleteProfileFormValues = z.infer<
  ReturnType<typeof createCompleteProfileSchema>
>;
export type ApiCompleteProfileData = Omit<
  CompleteProfileFormValues,
  "profile_picture"
> & {
  profile_picture?: File | null;
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
    identifier: z.string(), // Usually pre-filled, no validation message needed from schema
    otp: z
      .string()
      .min(6, { message: t("otpMinLength") })
      .max(6, { message: t("otpMaxLength") }) // Redundant with min(6) if regex also checks length
      .regex(/^\d{6}$/, { message: t("otpInvalidFormat") }),
  });
export type VerifyOtpFormValues = z.infer<
  ReturnType<typeof createVerifyOtpSchema>
>;

// --- Reset Password Schema ---
export const createResetPasswordSchema = (t: AuthTFunction) =>
  z
    .object({
      reset_token: z.string(), // Pre-filled
      new_password: z
        .string()
        .min(8, { message: t("newPasswordMinLength") })
        .regex(
          /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&._-])[A-Za-z\d@$!%*?&._-]+$/,
          { message: t("passwordComplexity") } // Reusing existing key
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
