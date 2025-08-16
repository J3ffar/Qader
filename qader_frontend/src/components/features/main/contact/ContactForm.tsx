"use client";

import React, { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { gsap } from "gsap";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { FolderOpenIcon, PaperAirplaneIcon } from "@heroicons/react/24/outline";
import { apiClient } from "@/services/apiClient";
import { setFormErrorsFromApi } from "@/utils/setFormErrorsFromApi";

// Define the form schema with Zod for validation
const formSchema = z.object({
  full_name: z.string().min(3, "الاسم يجب أن يكون 3 أحرف على الأقل."),
  email: z.string().email("الرجاء إدخال بريد إلكتروني صحيح."),
  subject: z.string().min(5, "الموضوع يجب أن يكون 5 أحرف على الأقل."),
  message: z.string().min(10, "الرسالة يجب أن تكون 10 أحرف على الأقل."),
  attachment: z.instanceof(File).optional().nullable(),
});

type ContactFormValues = z.infer<typeof formSchema>;

export const ContactForm = () => {
  // Refs for animations
  const formRef = useRef<HTMLDivElement>(null);
  const formFieldsRef = useRef<(HTMLDivElement | null)[]>([]);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const fileUploadRef = useRef<HTMLLabelElement>(null);

  const form = useForm<ContactFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      full_name: "",
      email: "",
      subject: "",
      message: "",
      attachment: null,
    },
  });

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set(formRef.current, {
        opacity: 0,
        scale: 0.95,
      });

      gsap.set(formFieldsRef.current, {
        opacity: 0,
        x: -30,
      });

      gsap.set(buttonRef.current, {
        opacity: 0,
        y: 20,
      });

      // Form container animation
      gsap.to(formRef.current, {
        opacity: 1,
        scale: 1,
        duration: 0.8,
        ease: "back.out(1.2)",
      });

      // Animate form fields with stagger
      gsap.to(formFieldsRef.current, {
        opacity: 1,
        x: 0,
        duration: 0.6,
        stagger: 0.1,
        ease: "power3.out",
        delay: 0.3,
      });

      // Animate button
      gsap.to(buttonRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.6,
        ease: "power2.out",
        delay: 0.8,
      });

      // Add floating animation to the form
      gsap.to(formRef.current, {
        y: -5,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 1,
      });

      // Input focus animations
      formFieldsRef.current.forEach((field) => {
        if (!field) return;
        
        const input = field.querySelector('input, textarea');
        if (!input) return;

        input.addEventListener('focus', () => {
          gsap.to(field, {
            scale: 1.02,
            duration: 0.3,
            ease: "power2.out",
          });
          
          // Add glow effect
          gsap.to(field, {
            boxShadow: "0 0 20px rgba(7, 65, 130, 0.15)",
            duration: 0.3,
          });
        });

        input.addEventListener('blur', () => {
          gsap.to(field, {
            scale: 1,
            duration: 0.3,
            ease: "power2.out",
            boxShadow: "none",
          });
        });
      });

      // File upload hover animation
      if (fileUploadRef.current) {
        fileUploadRef.current.addEventListener('mouseenter', () => {
          gsap.to(fileUploadRef.current, {
            scale: 1.02,
            borderColor: "#3b82f6",
            backgroundColor: "rgba(59, 130, 246, 0.05)",
            duration: 0.3,
            ease: "power2.out",
          });
        });

        fileUploadRef.current.addEventListener('mouseleave', () => {
          gsap.to(fileUploadRef.current, {
            scale: 1,
            borderColor: "#d1d5db",
            backgroundColor: "transparent",
            duration: 0.3,
            ease: "power2.out",
          });
        });

        // Drag and drop animations
        fileUploadRef.current.addEventListener('dragenter', (e) => {
          e.preventDefault();
          gsap.to(fileUploadRef.current, {
            scale: 1.05,
            borderColor: "#3b82f6",
            backgroundColor: "rgba(59, 130, 246, 0.1)",
            duration: 0.3,
            ease: "power2.out",
          });
        });

        fileUploadRef.current.addEventListener('dragleave', (e) => {
          e.preventDefault();
          gsap.to(fileUploadRef.current, {
            scale: 1,
            borderColor: "#d1d5db",
            backgroundColor: "transparent",
            duration: 0.3,
            ease: "power2.out",
          });
        });
      }

      // Button hover animation
      if (buttonRef.current) {
        buttonRef.current.addEventListener('mouseenter', () => {
          gsap.to(buttonRef.current, {
            scale: 1.05,
            duration: 0.2,
            ease: "power2.out",
          });
          
          const icon = buttonRef.current?.querySelector('.airplane-icon');
          if (icon) {
            gsap.to(icon, {
              x: 3,
              y: -3,
              rotation: -15,
              duration: 0.3,
              ease: "power2.out",
            });
          }
        });

        buttonRef.current.addEventListener('mouseleave', () => {
          gsap.to(buttonRef.current, {
            scale: 1,
            duration: 0.2,
            ease: "power2.out",
          });
          
          const icon = buttonRef.current?.querySelector('.airplane-icon');
          if (icon) {
            gsap.to(icon, {
              x: 0,
              y: 0,
              rotation: 0,
              duration: 0.3,
              ease: "power2.out",
            });
          }
        });
      }

      // Add subtle particle effect
      const createParticle = () => {
        const particle = document.createElement('div');
        particle.className = 'form-particle';
        formRef.current?.appendChild(particle);
        
        gsap.set(particle, {
          position: 'absolute',
          width: '4px',
          height: '4px',
          backgroundColor: '#074182',
          borderRadius: '50%',
          left: `${Math.random() * 100}%`,
          bottom: '0',
          opacity: 0.3,
          zIndex: -1,
        });

        gsap.to(particle, {
          y: -formRef.current!.offsetHeight - 50,
          opacity: 0,
          duration: 3,
          ease: "power1.out",
          onComplete: () => particle.remove(),
        });
      };

      // Create particles periodically
      const particleInterval = setInterval(createParticle, 2000);

      return () => {
        clearInterval(particleInterval);
      };
    }, formRef);

    return () => {
      ctx.revert();
    };
  }, []);

  const onSubmit = async (values: ContactFormValues) => {
    // Animate button during submission
    if (buttonRef.current) {
      gsap.to(buttonRef.current, {
        scale: 0.95,
        duration: 0.1,
        yoyo: true,
        repeat: 1,
        ease: "power2.inOut",
      });
    }

    const formData = new FormData();
    formData.append("full_name", values.full_name);
    formData.append("email", values.email);
    formData.append("subject", values.subject);
    formData.append("message", values.message);
    if (values.attachment) {
      formData.append("attachment", values.attachment);
    }

    const promise = apiClient("/content/contact-us/", {
      method: "POST",
      body: formData,
      isPublic: true,
    });

    toast.promise(promise, {
      loading: "جاري إرسال الرسالة...",
      success: (data: any) => {
        // Success animation
        gsap.to(formRef.current, {
          scale: 1.02,
          duration: 0.2,
          yoyo: true,
          repeat: 1,
          ease: "power2.inOut",
          onComplete: () => {
            form.reset();
            // Reset animations
            gsap.fromTo(formFieldsRef.current,
              { opacity: 0.5, scale: 0.95 },
              { opacity: 1, scale: 1, duration: 0.5, stagger: 0.05, ease: "power2.out" }
            );
          }
        });
        return data.detail || "تم إرسال رسالتك بنجاح!";
      },
      error: (error) => {
        // Error shake animation
        gsap.fromTo(formRef.current, 
          { x: 0 },
          {
            x: 10,
            duration: 0.1,
            repeat: 5,
            yoyo: true,
            ease: "power2.inOut",
            onComplete: () => {
              gsap.set(formRef.current, { x: 0 });
            }
          }
        );
        setFormErrorsFromApi(error, form.setError);
        return error.message || "فشل إرسال الرسالة. يرجى التحقق من البيانات.";
      },
    });
  };

  return (
    <div 
      ref={formRef}
      className="max-w-lg mx-auto p-6 bg-white dark:bg-[#0B1739] shadow-xl rounded-lg flex-1 relative overflow-hidden transform-gpu"
      style={{ perspective: "1000px" }}
    >
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#074182]/5 via-transparent to-[#e78b48]/5 opacity-50 pointer-events-none" />
      
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 relative z-10">
          <FormField
            control={form.control}
            name="full_name"
            render={({ field }) => (
              <FormItem>
                <div ref={(el) => { formFieldsRef.current[0] = el; }} className="transform-gpu">
                  <FormLabel className="text-gray-700 dark:text-gray-200 font-bold my-3">الاسم بالكامل</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="ادخل اسمك الكامل" 
                      {...field}
                      className="transition-all duration-300 hover:border-[#074182] focus:border-[#074182]"
                    />
                  </FormControl>
                  <FormMessage />
                </div>
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <div ref={(el) => { formFieldsRef.current[1] = el; }} className="transform-gpu">
                  <FormLabel className="text-gray-700 dark:text-gray-200 font-bold my-3">البريد الإلكتروني</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="ادخل بريدك الإلكتروني"
                      {...field}
                      className="transition-all duration-300 hover:border-[#074182] focus:border-[#074182]"
                    />
                  </FormControl>
                  <FormMessage />
                </div>
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="subject"
            render={({ field }) => (
              <FormItem>
                <div ref={(el) => { formFieldsRef.current[2] = el; }} className="transform-gpu">
                  <FormLabel className="text-gray-700 dark:text-gray-200 font-bold my-3">عنوان الموضوع</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="ادخل عنوان الموضوع" 
                      {...field}
                      className="transition-all duration-300 hover:border-[#074182] focus:border-[#074182]"
                    />
                  </FormControl>
                  <FormMessage />
                </div>
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="message"
            render={({ field }) => (
              <FormItem>
                <div ref={(el) => { formFieldsRef.current[3] = el; }} className="transform-gpu">
                  <FormLabel className="text-gray-700 dark:text-gray-200 font-bold my-3">الرسالة</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="اكتب رسالتك هنا..."
                      rows={5}
                      {...field}
                      className="transition-all duration-300 hover:border-[#074182] focus:border-[#074182] resize-none"
                    />
                  </FormControl>
                  <FormMessage />
                </div>
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="attachment"
            render={({ field: { onChange, value, ...rest } }) => (
              <FormItem>
                <div ref={(el) => { formFieldsRef.current[4] = el; }} className="transform-gpu">
                  <FormLabel className="text-gray-700 dark:text-gray-200 font-bold my-3">إرفاق ملف (اختياري)</FormLabel>
                  <FormControl>
                    <label
                      ref={fileUploadRef}
                      htmlFor="file-upload"
                      className="flex items-center justify-center gap-2 w-full h-32 px-4 py-6 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-md cursor-pointer hover:border-blue-400 bg-gray-50 dark:bg-transparent transition-all duration-300 transform-gpu group"
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        const files = e.dataTransfer.files;
                        if (files.length > 0) {
                          onChange(files[0]);
                        }
                      }}
                    >
                      <FolderOpenIcon className="h-6 w-6 text-gray-500 group-hover:text-blue-500 transition-colors duration-300 group-hover:scale-110 transform" />
                      <span className="text-gray-600 dark:text-gray-400 group-hover:text-blue-500 transition-colors duration-300">
                        {value?.name ? value.name : "اختر ملفاً أو اسحبه هنا"}
                      </span>
                      <Input
                        id="file-upload"
                        type="file"
                        className="hidden"
                        onChange={(e) =>
                          onChange(e.target.files ? e.target.files[0] : null)
                        }
                        {...rest}
                      />
                    </label>
                  </FormControl>
                  <FormMessage />
                </div>
              </FormItem>
            )}
          />
          <Button
            ref={buttonRef}
            type="submit"
            className="w-full flex items-center justify-center gap-2 bg-[#074182] hover:bg-[#053061] text-white font-medium py-3 rounded-lg transition-all duration-300 transform-gpu relative overflow-hidden group"
            disabled={form.formState.isSubmitting}
          >
            <span className="relative z-10">
              {form.formState.isSubmitting ? "جاري الإرسال..." : "إرسال"}
            </span>
            {!form.formState.isSubmitting && (
              <PaperAirplaneIcon className="airplane-icon h-5 w-5 relative z-10 transform-gpu" />
            )}
            
            {/* Button shine effect */}
            <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-1000 ease-out" />
          </Button>
        </form>
      </Form>
    </div>
  );
};
