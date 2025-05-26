import { z } from "zod";

// --- Login Schema ---
const requiredField = (fieldName: string) => `حقل ${fieldName} مطلوب`; // Reusable helper

export const LoginSchema = z.object({
  username: z
    .string()
    .min(1, { message: requiredField("اسم المستخدم أو البريد الإلكتروني") })
    // Allow either email or a username string
    .refine(
      (value) =>
        z.string().email().safeParse(value).success ||
        /^[a-zA-Z0-9_.-]+$/.test(value),
      {
        message:
          "الرجاء إدخال بريد إلكتروني صالح أو اسم مستخدم صالح (أحرف، أرقام، _، ., -)",
      }
    ),
  password: z.string().min(1, { message: requiredField("كلمة المرور") }),
  rememberMe: z.boolean().optional(),
});
export type LoginCredentials = z.infer<typeof LoginSchema>;

// --- Signup Schema with Detailed Arabic Error Messages ---
export const SignupSchema = z
  .object({
    full_name: z
      .string()
      .min(3, { message: "يجب أن يتكون الاسم الكامل من 3 أحرف على الأقل." })
      .max(100, { message: "يجب ألا يتجاوز الاسم الكامل 100 حرف." })
      .regex(/^[ \p{L}\p{M}'-]+$/u, {
        // Allows letters from any language, spaces, hyphens, apostrophes
        message: "الاسم الكامل يحتوي على أحرف غير صالحة. استخدم الأحرف فقط.",
      }),
    email: z
      .string()
      .min(1, { message: requiredField("البريد الإلكتروني") })
      .email({
        message:
          "الرجاء إدخال عنوان بريد إلكتروني صالح (مثال: user@example.com).",
      }),
    password: z
      .string()
      .min(8, { message: "يجب أن تتكون كلمة المرور من 8 أحرف على الأقل." })
      .max(128, { message: "يجب ألا تتجاوز كلمة المرور 128 حرفًا." })
      // Example: Require at least one letter, one number, and one special character
      .regex(
        /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&._-])[A-Za-z\d@$!%*?&._-]+$/,
        {
          message:
            "يجب أن تحتوي كلمة المرور على حرف واحد ورقم واحد ورمز خاص واحد على الأقل (@$!%*?&._-).",
        }
      ),
    password_confirm: z
      .string()
      .min(1, { message: requiredField("تأكيد كلمة المرور") }), // Basic check, main check is in .refine
    termsAccepted: z.boolean().refine((val) => val === true, {
      message: "يجب الموافقة على الشروط والأحكام للمتابعة.",
    }),
  })
  .refine((data) => data.password === data.password_confirm, {
    message: "كلمتا المرور غير متطابقتين. الرجاء التأكد من تطابقهما.",
    path: ["password_confirm"], // Apply error to the password_confirm field
  });

// Type for the form itself, including termsAccepted
export type SignupFormValues = z.infer<typeof SignupSchema>;

// Type for the data to be sent to the API (omitting termsAccepted as it's a UI concern)
export type ApiSignupData = Omit<SignupFormValues, "termsAccepted">;

// Helper for profile picture validation
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ACCEPTED_IMAGE_TYPES = [
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
];

export const CompleteProfileSchema = z.object({
  gender: z.enum(["male", "female"], {
    required_error: "الرجاء اختيار الجنس.",
    invalid_type_error: "قيمة الجنس غير صالحة.",
  }),
  grade: z
    .string()
    .min(1, { message: "الرجاء إدخال الصف الدراسي." })
    .max(50, { message: "الصف الدراسي طويل جدًا." }),
  has_taken_qiyas_before: z.boolean({
    required_error: "الرجاء تحديد ما إذا كنت قد اختبرت قدرات من قبل.",
    invalid_type_error: "قيمة غير صالحة لخيار اختبار القدرات.",
  }),
  preferred_name: z
    .string()
    .max(100, { message: "الاسم المفضل طويل جدًا." })
    .optional()
    .nullable(),
  profile_picture: z
    .custom<FileList>() // For FileList from input type="file"
    .refine(
      (files) =>
        files === undefined ||
        files === null ||
        files.length === 0 ||
        files?.[0]?.size <= MAX_FILE_SIZE,
      `يجب أن يكون حجم الصورة أقل من 5 ميجابايت.`
    )
    .refine(
      (files) =>
        files === undefined ||
        files === null ||
        files.length === 0 ||
        (files?.[0]?.type && ACCEPTED_IMAGE_TYPES.includes(files[0].type)),
      "صيغ الصور المدعومة هي .jpg, .jpeg, .png, .webp"
    )
    .optional()
    .nullable(),
  serial_code: z
    .string()
    .max(50, { message: "الرمز التسلسلي طويل جدًا." })
    .optional()
    .nullable(),
  referral_code_used: z
    .string()
    .max(50, { message: "رمز الإحالة طويل جدًا." })
    .optional()
    .nullable(),
  language: z.enum(["ar", "en"], {
    required_error: "الرجاء اختيار اللغة.",
  }),
  // Note: 'username' was in your old form state but not in the API spec for PATCH /users/me/complete-profile/
  // The API for complete-profile does not seem to allow changing the username. Username is usually set at initial signup or is the email.
  // If you NEED to send username here, the API spec for this endpoint needs to be updated.
  // For now, I am omitting it from this schema as it's not in the PATCH request body.
});

// Type for the form values
export type CompleteProfileFormValues = z.infer<typeof CompleteProfileSchema>;

// Type for the data sent to the API (FormData compatible)
// For FormData, we usually don't have a strict Zod type for the payload itself,
// as RHF handles converting schema values to FormData entries.
// However, the service function will need the values.
export type ApiCompleteProfileData = Omit<
  CompleteProfileFormValues,
  "profile_picture"
> & {
  profile_picture?: File | null; // Explicitly File for the service
};

export const RequestOtpSchema = z.object({
  identifier: z // Can be email or username
    .string()
    .min(1, { message: "الرجاء إدخال البريد الإلكتروني أو اسم المستخدم." })
    // Optional: add more specific validation if you can distinguish email from username client-side
    .refine(
      (value) =>
        z.string().email().safeParse(value).success ||
        /^[a-zA-Z0-9_.-]+$/.test(value),
      {
        message: "الرجاء إدخال بريد إلكتروني صالح أو اسم مستخدم صالح.",
      }
    ),
});
export type RequestOtpFormValues = z.infer<typeof RequestOtpSchema>;

export const VerifyOtpSchema = z.object({
  identifier: z.string(), // Will be pre-filled from step 1
  otp: z
    .string()
    .min(6, { message: "يجب أن يتكون رمز OTP من 6 أرقام." })
    .max(6, { message: "يجب أن يتكون رمز OTP من 6 أرقام." })
    .regex(/^\d{6}$/, {
      message: "الرجاء إدخال رمز OTP صالح مكون من 6 أرقام.",
    }),
});
export type VerifyOtpFormValues = z.infer<typeof VerifyOtpSchema>;

export const ResetPasswordSchema = z
  .object({
    reset_token: z.string(), // Will be pre-filled from step 2
    new_password: z
      .string()
      .min(8, {
        message: "يجب أن تتكون كلمة المرور الجديدة من 8 أحرف على الأقل.",
      })
      .regex(
        /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&._-])[A-Za-z\d@$!%*?&._-]+$/,
        {
          // Same complexity as signup
          message:
            "يجب أن تحتوي كلمة المرور على حرف واحد ورقم واحد ورمز خاص واحد على الأقل (@$!%*?&._-).",
        }
      ),
    new_password_confirm: z
      .string()
      .min(1, { message: "الرجاء تأكيد كلمة المرور الجديدة." }),
  })
  .refine((data) => data.new_password === data.new_password_confirm, {
    message: "كلمتا المرور الجديدتان غير متطابقتين.",
    path: ["new_password_confirm"],
  });
export type ResetPasswordFormValues = z.infer<typeof ResetPasswordSchema>;
