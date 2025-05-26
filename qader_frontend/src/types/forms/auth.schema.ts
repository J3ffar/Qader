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
