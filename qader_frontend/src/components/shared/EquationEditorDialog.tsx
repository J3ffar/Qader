"use client";

import { useState } from "react";
import * as z from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Link } from "lucide-react";

const schema = z.object({
  latex: z.string().min(1, "صيغة LaTeX مطلوبة."),
});

interface EquationEditorDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (latex: string) => void;
  initialValue?: string;
}

export const EquationEditorDialog = ({
  isOpen,
  onClose,
  onSubmit,
  initialValue = "",
}: EquationEditorDialogProps) => {
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { latex: initialValue },
  });

  const handleInnerFormSubmit = (values: z.infer<typeof schema>) => {
    onSubmit(values.latex);
    onClose();
    form.reset();
  };

  const onFormSubmit = (e: React.FormEvent) => {
    e.preventDefault(); // Prevent default form submission
    e.stopPropagation(); // Stop the event from bubbling up to the parent form
    form.handleSubmit(handleInnerFormSubmit)(); // Manually trigger RHF's handler
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>إضافة / تعديل معادلة</DialogTitle>
          <DialogDescription>أدخل صيغة LaTeX للمعادلة أدناه.</DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <a
            href="https://editor.codecogs.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-blue-600 dark:text-blue-400 hover:underline mb-4"
          >
            <Link className="h-4 w-4 ltr:mr-1 rtl:ml-1" />
            استخدم محرر معادلات مرئي (يفتح في نافذة جديدة)
          </a>
          <Form {...form}>
            <form id="equation-form" onSubmit={onFormSubmit}>
              <FormField
                control={form.control}
                name="latex"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>صيغة LaTeX</FormLabel>
                    <FormControl>
                      <Textarea
                        {...field}
                        rows={4}
                        className="font-mono ltr:text-left"
                        dir="ltr"
                        placeholder="e.g. x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </form>
          </Form>
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            إلغاء
          </Button>
          <Button type="submit" form="equation-form">
            حفظ المعادلة
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
