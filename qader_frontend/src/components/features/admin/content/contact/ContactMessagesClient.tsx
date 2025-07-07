"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { format } from "date-fns";
import { arSA } from "date-fns/locale"; // Import Arabic locale for date-fns
import { Eye, Search } from "lucide-react";
import { useTranslations } from "next-intl";

import { queryKeys } from "@/constants/queryKeys";
import {
  getContactMessages,
  updateContactMessage,
  GetContactMessagesParams,
} from "@/services/api/admin/content.service";
import type { ContactMessage } from "@/types/api/admin/content.types";
import { useDebounce } from "@/hooks/use-debounce";
import { ITEMS_PER_PAGE } from "@/constants/config";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
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
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { cn } from "@/lib/utils";

const updateSchema = z.object({
  status: z.enum(["new", "read", "replied", "archived"]),
  response: z.string().optional(),
});
type UpdateFormValues = z.infer<typeof updateSchema>;

export function ContactMessagesClient() {
  const t = useTranslations("Admin.Content.contact");
  const queryClient = useQueryClient();
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<ContactMessage | null>(
    null
  );

  // Dynamically create status options from translations
  const statusOptions = useMemo(
    () =>
      [
        { value: "new", label: t("statusLabels.new") },
        { value: "read", label: t("statusLabels.read") },
        { value: "replied", label: t("statusLabels.replied") },
        { value: "archived", label: t("statusLabels.archived") },
      ] as const,
    [t]
  );

  const [filters, setFilters] = useState<
    Omit<GetContactMessagesParams, "page">
  >({
    search: "",
    status: "",
    ordering: "-created_at",
  });
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebounce(filters.search ?? "", 300);

  const queryParams = useMemo(
    () => ({
      page,
      page_size: ITEMS_PER_PAGE,
      ...filters,
      search: debouncedSearch,
    }),
    [page, filters, debouncedSearch]
  );

  const {
    data: response,
    isLoading,
    isFetching,
  } = useQuery({
    // Destructure isFetching
    queryKey: queryKeys.admin.content.contact.list(queryParams),
    queryFn: () => getContactMessages(queryParams),
    placeholderData: (prev) => prev,
  });
  const messages = response?.results ?? [];
  const pageCount = response ? Math.ceil(response.count / ITEMS_PER_PAGE) : 0;

  // *** THE FIX IS HERE ***
  // Calculate the pagination state based on current page and total page count.
  const canPreviousPage = page > 1;
  const canNextPage = page < pageCount;

  const form = useForm<UpdateFormValues>({
    resolver: zodResolver(updateSchema),
  });

  const updateMutation = useMutation({
    mutationFn: updateContactMessage,
    onSuccess: (updatedMessage) => {
      toast.success(t("toast.updateSuccess"));
      queryClient.setQueryData(
        queryKeys.admin.content.contact.list(queryParams),
        (oldData: any) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            results: oldData.results.map((msg: ContactMessage) =>
              msg.id === updatedMessage.id ? updatedMessage : msg
            ),
          };
        }
      );
      setDialogOpen(false);
    },
    onError: (err) =>
      toast.error(t("toast.updateError"), { description: err.message }),
  });

  const handleOpenDialog = (message: ContactMessage) => {
    setSelectedMessage(message);
    form.reset({ status: message.status, response: message.response ?? "" });
    // If status is 'new', optimistically update it to 'read'
    if (message.status === "new") {
      updateMutation.mutate({ id: message.id, payload: { status: "read" } });
    }
    setDialogOpen(true);
  };

  const onSubmit = (values: UpdateFormValues) => {
    if (selectedMessage) {
      updateMutation.mutate({ id: selectedMessage.id, payload: values });
    }
  };

  const handleFilterChange = (key: keyof typeof filters, value: string) => {
    const finalValue = value === "all" ? "" : value;
    setFilters((prev) => ({ ...prev, [key]: finalValue }));
    setPage(1); // Reset to first page on filter change
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>{t("cardTitle")}</CardTitle>
          <div className="mt-4 flex items-center gap-2">
            <div className="relative w-full">
              <Search className="absolute rtl:right-2.5 ltr:left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t("searchPlaceholder")}
                className="rtl:pr-8 ltr:pl-8"
                value={filters.search}
                onChange={(e) => handleFilterChange("search", e.target.value)}
              />
            </div>
            <Select
              value={filters.status || "all"}
              onValueChange={(value) => handleFilterChange("status", value)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={t("filterPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("allStatuses")}</SelectItem>
                {statusOptions.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("table.from")}</TableHead>
                  <TableHead>{t("table.subject")}</TableHead>
                  <TableHead className="hidden md:table-cell">
                    {t("table.date")}
                  </TableHead>
                  <TableHead>{t("table.status")}</TableHead>
                  <TableHead>
                    <span className="sr-only">{t("table.actions")}</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading &&
                  Array.from({ length: 10 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell colSpan={5}>
                        <Skeleton className="h-8 w-full" />
                      </TableCell>
                    </TableRow>
                  ))}
                {messages.map((message) => (
                  <TableRow
                    key={message.id}
                    className={cn(
                      message.status === "new" && "bg-muted/50 font-bold"
                    )}
                  >
                    <TableCell>
                      <div>{message.full_name}</div>
                      <div className="text-xs text-muted-foreground">
                        {message.email}
                      </div>
                    </TableCell>
                    <TableCell>{message.subject}</TableCell>
                    <TableCell className="hidden md:table-cell">
                      {format(new Date(message.created_at), "PPp", {
                        locale: arSA,
                      })}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          message.status === "new" ? "default" : "secondary"
                        }
                      >
                        {t(`statusLabels.${message.status}`)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handleOpenDialog(message)}
                      >
                        <Eye className="h-4 w-4" />
                        <span className="sr-only">{t("viewMessage")}</span>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <DataTablePagination
            page={page}
            pageCount={pageCount}
            setPage={setPage}
            canPreviousPage={canPreviousPage}
            canNextPage={canNextPage}
            isFetching={isFetching}
          />
        </CardContent>
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedMessage?.subject}</DialogTitle>
            <DialogDescription>
              {t("dialog.fromLabel")}: {selectedMessage?.full_name} &lt;
              {selectedMessage?.email}&gt;
              <br />
              {t("dialog.receivedLabel")}:{" "}
              {selectedMessage &&
                format(new Date(selectedMessage.created_at), "PPp", {
                  locale: arSA,
                })}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4 max-h-[60vh] overflow-y-auto px-1">
            <p className="whitespace-pre-wrap text-sm">
              {selectedMessage?.message}
            </p>
            {selectedMessage?.attachment && (
              <Button asChild variant="outline" size="sm">
                <a
                  href={selectedMessage.attachment}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t("dialog.viewAttachment")}
                </a>
              </Button>
            )}
            <Form {...form}>
              <form
                id="update-message-form"
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4 pt-4 border-t"
              >
                <FormField
                  name="status"
                  control={form.control}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("dialog.updateStatusLabel")}</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue
                              placeholder={t("dialog.selectStatusPlaceholder")}
                            />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {statusOptions.map((s) => (
                            <SelectItem key={s.value} value={s.value}>
                              {s.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </form>
            </Form>
          </div>
          <DialogFooter>
            <Button
              type="submit"
              form="update-message-form"
              disabled={updateMutation.isPending}
            >
              {t("dialog.saveButton")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
