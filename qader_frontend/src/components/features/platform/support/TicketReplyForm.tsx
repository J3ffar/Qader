// src/components/features/platform/support/TicketReplyForm.tsx
"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { addTicketReply } from "@/services/support.service";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Send, Paperclip, X } from "lucide-react";
import type {
  OptimisticSupportTicketReply,
  SupportTicketDetail,
  AddReplyPayload,
} from "@/types/api/support.types";
import { useAuthStore } from "@/store/auth.store";
import { useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_FILE_TYPES = [
  "image/jpeg",
  "image/png",
  "image/gif",
  "image/webp",
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];

const formSchema = z.object({
  message: z.string().min(1, "لا يمكن إرسال رسالة فارغة."),
  attachments: z
    .array(z.instanceof(File))
    .optional()
    .refine(
      (files) => {
        if (!files) return true;
        return files.every((file) => file.size <= MAX_FILE_SIZE);
      },
      "حجم الملف يجب أن يكون أقل من 10 ميجابايت"
    )
    .refine(
      (files) => {
        if (!files) return true;
        return files.every((file) => ALLOWED_FILE_TYPES.includes(file.type));
      },
      "نوع الملف غير مدعوم"
    ),
});

interface TicketReplyFormProps {
  ticketId: number | string;
  isTicketClosed: boolean;
}

// Interface for file attachment display
interface FileAttachmentDisplay {
  name: string;
  size: number;
  type: string;
}

// Helper function to format file size
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
};

// Helper function to get file icon based on type
const getFileIcon = (fileType: string): string => {
  if (fileType.startsWith("image/")) return "🖼️";
  if (fileType === "application/pdf") return "📄";
  if (fileType.includes("word")) return "📝";
  return "📎";
};

// Extended OptimisticSupportTicketReply interface with attachments
interface ExtendedOptimisticSupportTicketReply extends OptimisticSupportTicketReply {
  attachments?: FileAttachmentDisplay[];
}

export function TicketReplyForm({
  ticketId,
  isTicketClosed,
}: TicketReplyFormProps) {
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((state) => state.user);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { 
      message: "",
      attachments: []
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    
    // Validate files
    const validFiles = files.filter((file) => {
      if (file.size > MAX_FILE_SIZE) {
        toast.error(`الملف "${file.name}" كبير جداً. الحد الأقصى 10 ميجابايت`);
        return false;
      }
      if (!ALLOWED_FILE_TYPES.includes(file.type)) {
        toast.error(`نوع الملف "${file.name}" غير مدعوم`);
        return false;
      }
      return true;
    });

    if (validFiles.length > 0) {
      const newFiles = [...selectedFiles, ...validFiles];
      setSelectedFiles(newFiles);
      form.setValue("attachments", newFiles, { shouldValidate: true });
    }
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removeFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(newFiles);
    form.setValue("attachments", newFiles, { shouldValidate: true });
  };

  const addReplyMutation = useMutation({
    mutationFn: async (payload: { message: string; attachments?: File[] }) => {
      // Create the proper payload structure based on your AddReplyPayload type
      const replyPayload: AddReplyPayload = {
        message: payload.message,
        // Add other required fields from AddReplyPayload if needed
        // attachments: payload.attachments, // Only if AddReplyPayload supports attachments directly
      };

      // If your API expects FormData, create it here
      const formData = new FormData();
      formData.append("message", payload.message);
      
      if (payload.attachments && payload.attachments.length > 0) {
        payload.attachments.forEach((file) => {
          formData.append("attachments", file);
        });
      }
      
      // Use FormData if your service expects it, otherwise use replyPayload
      // Adjust this based on your actual service implementation
      return addTicketReply({ 
        ticketId, 
        payload: formData as any // Type assertion if FormData is expected but types don't match
      });
    },
    onMutate: async (newReply) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.user.support.detail(ticketId),
      });

      const previousTicket = queryClient.getQueryData<SupportTicketDetail>(
        queryKeys.user.support.detail(ticketId)
      );

      if (!currentUser) {
        toast.error("حدث خطأ، المستخدم الحالي غير معروف.");
        return { previousTicket };
      }

      const optimisticReply: ExtendedOptimisticSupportTicketReply = {
        id: Date.now(),
        message: newReply.message,
        user: {
          id: currentUser.id,
          username: currentUser.username,
          full_name: currentUser.full_name,
          preferred_name: currentUser.preferred_name,
          profile_picture_url: currentUser.profile_picture_url,
          grade: currentUser.grade,
        },
        created_at: new Date().toISOString(),
        optimistic: true,
        status: "sending",
        attachments: newReply.attachments?.map(file => ({
          name: file.name,
          size: file.size,
          type: file.type,
        })),
      };

      queryClient.setQueryData<SupportTicketDetail>(
        queryKeys.user.support.detail(ticketId),
        (oldTicketData) => {
          if (!oldTicketData) {
            return undefined;
          }

          return {
            ...oldTicketData,
            replies: [
              ...oldTicketData.replies,
              optimisticReply as OptimisticSupportTicketReply, // Type assertion
            ],
          };
        }
      );

      form.reset();
      setSelectedFiles([]);
      return { previousTicket };
    },
    onError: (error, _newReply, context) => {
      toast.error(getApiErrorMessage(error, "فشل إرسال الرد."));

      if (context?.previousTicket) {
        queryClient.setQueryData(
          queryKeys.user.support.detail(ticketId),
          context.previousTicket
        );
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.user.support.detail(ticketId),
      });
      toast.success("تم إرسال الرد بنجاح");
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    if (!currentUser) return toast.error("يجب تسجيل الدخول لإرسال رد.");
    addReplyMutation.mutate({
      message: values.message,
      attachments: values.attachments,
    });
  }

  if (isTicketClosed) {
    return (
      <div className="p-4 border-t text-center bg-muted">
        <p className="text-muted-foreground">
          تم إغلاق هذه المحادثة ولا يمكن إضافة ردود جديدة.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 border-t bg-card">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="space-y-4"
          dir="rtl"
        >
          {/* Selected Files Display */}
          {selectedFiles.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {selectedFiles.map((file, index) => (
                <Badge
                  key={index}
                  variant="secondary"
                  className="flex items-center gap-2 py-1.5 px-3"
                >
                  <span>{getFileIcon(file.type)}</span>
                  <span className="max-w-[200px] truncate">{file.name}</span>
                  <span className="text-xs text-muted-foreground">
                    ({formatFileSize(file.size)})
                  </span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 hover:bg-transparent"
                    onClick={() => removeFile(index)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              ))}
            </div>
          )}

          <div className="flex items-end gap-2">
            <FormField
              control={form.control}
              name="message"
              render={({ field }) => (
                <FormItem className="flex-1">
                  <FormControl>
                    <Textarea
                      placeholder="اكتب رسالتك هنا..."
                      {...field}
                      rows={3}
                      className="min-h-[80px] resize-none"
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          form.handleSubmit(onSubmit)();
                        }
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <div className="flex gap-2">
              {/* File Input Button */}
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => fileInputRef.current?.click()}
                disabled={addReplyMutation.isPending}
              >
                <Paperclip className="h-5 w-5" />
              </Button>
              
              {/* Hidden File Input */}
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept={ALLOWED_FILE_TYPES.join(",")}
                onChange={handleFileSelect}
                className="hidden"
              />
              
              {/* Send Button */}
              <Button 
                type="submit" 
                disabled={addReplyMutation.isPending || (!form.watch("message") && selectedFiles.length === 0)}
              >
                <Send className="h-5 w-5" />
              </Button>
            </div>
          </div>
          
          {/* File Type Hint */}
          <p className="text-xs text-muted-foreground">
            الملفات المدعومة: الصور (JPEG, PNG, GIF, WebP)، PDF، Word، نصوص عادية. الحد الأقصى: 10 ميجابايت
          </p>
        </form>
      </Form>
    </div>
  );
}
