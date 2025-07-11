"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { zodResolver } from "@hookform/resolvers/zod";
import { Search } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

const searchSchema = z.object({
  name: z.string().optional(),
  grade: z.string().optional(),
});

type SearchFilters = z.infer<typeof searchSchema>;

interface SearchPartnerDialogProps {
  onSearch: (filters: SearchFilters) => void;
}

export function SearchPartnerDialog({ onSearch }: SearchPartnerDialogProps) {
  const form = useForm<SearchFilters>({
    resolver: zodResolver(searchSchema),
    defaultValues: { name: "", grade: "" },
  });

  const onSubmit = (values: SearchFilters) => {
    onSearch(values);
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Search className="me-2 h-4 w-4" />
          بحث عن زميل
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>البحث عن زميل</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>اسم المستخدم</FormLabel>
                  <FormControl>
                    <Input placeholder="اكتب اسم المستخدم..." {...field} />
                  </FormControl>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="grade"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>حدد المستوى</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="الكل" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="ثالث ثانوي">ثالث ثانوي</SelectItem>
                      <SelectItem value="ثاني ثانوي">ثاني ثانوي</SelectItem>
                      <SelectItem value="أول ثانوي">أول ثانوي</SelectItem>
                    </SelectContent>
                  </Select>
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full">
              بحث
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
