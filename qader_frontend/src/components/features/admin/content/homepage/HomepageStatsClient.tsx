"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { MoreHorizontal, PlusCircle } from "lucide-react";

import { queryKeys } from "@/constants/queryKeys";
import {
  createHomepageStat,
  deleteHomepageStat,
  getHomepageStats,
  updateHomepageStat,
} from "@/services/api/admin/content.service";
import type { HomepageStatistic } from "@/types/api/admin/content.types";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
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
import { Switch } from "@/components/ui/switch";
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";

// Zod Schema for validation
const statSchema = z.object({
  label: z.string().min(3, "Label is required."),
  value: z.string().min(1, "Value is required."),
  icon_class: z.string().optional().nullable(),
  order: z.coerce.number().int().min(0),
  is_active: z.boolean(),
});
type StatFormValues = z.infer<typeof statSchema>;

export function HomepageStatsClient() {
  const queryClient = useQueryClient();
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [selectedStat, setSelectedStat] = useState<HomepageStatistic | null>(
    null
  );

  const { data: response, isLoading } = useQuery({
    queryKey: queryKeys.admin.content.homepage.stats(),
    queryFn: getHomepageStats,
  });
  const stats = response?.results ?? [];

  const form = useForm<StatFormValues>({
    resolver: zodResolver(statSchema),
    defaultValues: {
      label: "",
      value: "",
      icon_class: "",
      order: 0,
      is_active: true,
    },
  });

  // --- MUTATIONS ---
  const createMutation = useMutation({
    mutationFn: createHomepageStat,
    onSuccess: () => {
      toast.success("Statistic created successfully!");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.stats(),
      });
      setDialogOpen(false);
    },
    onError: (err) =>
      toast.error("Failed to create statistic.", { description: err.message }),
  });

  const updateMutation = useMutation({
    mutationFn: updateHomepageStat,
    onSuccess: () => {
      toast.success("Statistic updated successfully!");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.stats(),
      });
      setDialogOpen(false);
    },
    onError: (err) =>
      toast.error("Failed to update statistic.", { description: err.message }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteHomepageStat,
    onSuccess: () => toast.success("Statistic deleted."),
    onMutate: async (idToDelete) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.admin.content.homepage.stats(),
      });
      const previousStats = queryClient.getQueryData<any>(
        queryKeys.admin.content.homepage.stats()
      );
      queryClient.setQueryData(
        queryKeys.admin.content.homepage.stats(),
        (old: any) => ({
          ...old,
          results: old.results.filter(
            (s: HomepageStatistic) => s.id !== idToDelete
          ),
        })
      );
      return { previousStats };
    },
    onError: (err, _vars, context) => {
      queryClient.setQueryData(
        queryKeys.admin.content.homepage.stats(),
        context?.previousStats
      );
      toast.error("Failed to delete statistic.", { description: err.message });
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.content.homepage.stats(),
      });
    },
  });

  // --- HANDLERS ---
  const handleOpenDialog = (stat: HomepageStatistic | null = null) => {
    setSelectedStat(stat);
    if (stat) {
      form.reset(stat);
    } else {
      form.reset({
        label: "",
        value: "",
        icon_class: "",
        order: stats.length,
        is_active: true,
      });
    }
    setDialogOpen(true);
  };

  const onSubmit = (values: StatFormValues) => {
    if (selectedStat) {
      updateMutation.mutate({ id: selectedStat.id, payload: values });
    } else {
      createMutation.mutate(values as any);
    }
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>Homepage Statistics</CardTitle>
              <CardDescription>
                Items appearing in the animated stats bar.
              </CardDescription>
            </div>
            <Button onClick={() => handleOpenDialog()}>
              <PlusCircle className="ltr:mr-2 rtl:ml-2 h-4 w-4" /> Add New Stat
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Order</TableHead>
                  <TableHead>Label</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading &&
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell>
                        <Skeleton className="h-5 w-8" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-5 w-32" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-5 w-24" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-6 w-16" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-8 w-8" />
                      </TableCell>
                    </TableRow>
                  ))}
                {stats.map((stat) => (
                  <TableRow key={stat.id}>
                    <TableCell>{stat.order}</TableCell>
                    <TableCell className="font-medium">{stat.label}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {stat.value}
                    </TableCell>
                    <TableCell>
                      <Badge variant={stat.is_active ? "default" : "secondary"}>
                        {stat.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu modal={false}>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem
                            onClick={() => handleOpenDialog(stat)}
                          >
                            Edit
                          </DropdownMenuItem>
                          <ConfirmationDialog
                            triggerButton={
                              <DropdownMenuItem
                                className="text-destructive"
                                onSelect={(e) => e.preventDefault()}
                              >
                                Delete
                              </DropdownMenuItem>
                            }
                            title="Delete Statistic"
                            description={`Are you sure you want to delete the statistic "${stat.label}"?`}
                            onConfirm={() => deleteMutation.mutate(stat.id)}
                            isConfirming={
                              deleteMutation.isPending &&
                              selectedStat?.id === stat.id
                            }
                          />
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
      <Dialog open={isDialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>
              {selectedStat ? "Edit Statistic" : "Create New Statistic"}
            </DialogTitle>
          </DialogHeader>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4 py-4"
            >
              <FormField
                name="label"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Label</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="value"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Value</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="icon_class"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Icon Class</FormLabel>
                    <FormControl>
                      <Input {...field} value={field.value ?? ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="order"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Display Order</FormLabel>
                    <FormControl>
                      <Input type="number" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="is_active"
                control={form.control}
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-lg border p-3">
                    <FormLabel>Active</FormLabel>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button
                  type="submit"
                  disabled={
                    createMutation.isPending || updateMutation.isPending
                  }
                >
                  Save
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </>
  );
}
