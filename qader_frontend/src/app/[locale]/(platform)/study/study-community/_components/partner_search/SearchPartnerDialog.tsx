import { useState } from "react";
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
import { grades } from "@/constants/config"; // <-- **IMPORT GRADES**

const searchSchema = z.object({
  name: z.string().optional(),
  grade: z.string().optional(),
});

type SearchFilters = z.infer<typeof searchSchema>;

interface SearchPartnerDialogProps {
  onSearch: (filters: SearchFilters) => void;
}

export function SearchPartnerDialog({ onSearch }: SearchPartnerDialogProps) {
  const [isOpen, setIsOpen] = useState(false); // <-- **STATE TO CONTROL DIALOG**

  const form = useForm<SearchFilters>({
    resolver: zodResolver(searchSchema),
    defaultValues: { name: "", grade: "" },
  });

  const onSubmit = (values: SearchFilters) => {
    onSearch(values);
    setIsOpen(false); // <-- **CLOSE DIALOG ON SUBMIT**
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
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
                      {/* ** DYNAMICALLY RENDER GRADES ** */}
                      {grades.map((grade) => (
                        <SelectItem key={grade} value={grade}>
                          {grade}
                        </SelectItem>
                      ))}
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
