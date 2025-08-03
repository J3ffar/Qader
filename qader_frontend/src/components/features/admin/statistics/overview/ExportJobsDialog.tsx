import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Clock,
  CheckCircle2,
  XCircle,
  Download,
  RefreshCcw,
} from "lucide-react";
import { formatDate, formatDistanceToNow } from "date-fns";
import { ar } from "date-fns/locale";

import { getExportJobs } from "@/services/api/admin/statistics.service";
import { queryKeys } from "@/constants/queryKeys";
import { type ExportJob } from "@/types/api/admin/statistics.types";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Skeleton } from "@/components/ui/skeleton";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"; // Import Tabs

type JobType = "TEST_ATTEMPTS" | "USERS";

interface ExportJobsDialogProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  initialJobType?: JobType;
}
const PAGE_SIZE = 20;

const formatJobFilters = (filters: ExportJob["filters"]): string => {
  if (!filters.datetime_from && !filters.datetime_to) {
    return "الكل"; // All
  }
  const from = filters.datetime_from
    ? formatDate(new Date(filters.datetime_from), "dd/MM/yyyy")
    : "...";
  const to = filters.datetime_to
    ? formatDate(new Date(filters.datetime_to), "dd/MM/yyyy")
    : "...";
  return `${from} - ${to}`;
};

// --- Helper function to calculate and format duration ---
const formatJobDuration = (
  createdAt: string,
  completedAt: string | null
): string => {
  if (!completedAt) {
    return "-";
  }
  const start = new Date(createdAt);
  const end = new Date(completedAt);
  const durationInSeconds = (end.getTime() - start.getTime()) / 1000;

  if (durationInSeconds < 1) {
    return "أقل من ثانية";
  }
  return `${Math.round(durationInSeconds)} ثانية`;
};

const JobStatus = ({
  status,
  errorMessage,
}: {
  status: ExportJob["status"];
  errorMessage: ExportJob["error_message"];
}) => {
  const statusConfig = {
    Pending: {
      icon: <Clock className="me-1.5 h-3.5 w-3.5" />,
      text: "قيد المعالجة",
      variant: "secondary",
    },
    "In Progress": {
      icon: <Clock className="me-1.5 h-3.5 w-3.5" />,
      text: "جاري التنفيذ",
      variant: "secondary",
    },
    Success: {
      icon: <CheckCircle2 className="me-1.5 h-3.5 w-3.5 text-green-500" />,
      text: "نجحت",
      variant: "outline",
    },
    Failure: {
      icon: <XCircle className="me-1.5 h-3.5 w-3.5 text-red-500" />,
      text: "فشلت",
      variant: "destructive",
    },
  } as const;

  const config = statusConfig[status] || statusConfig.Pending;

  if (status === "Failure" && errorMessage) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger>
            <Badge variant={config.variant} className="cursor-help">
              {config.icon}
              {config.text}
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>سبب الفشل: {errorMessage}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <Badge variant={config.variant}>
      {config.icon}
      {config.text}
    </Badge>
  );
};

export function ExportJobsDialog({
  isOpen,
  onOpenChange,
  initialJobType,
}: ExportJobsDialogProps) {
  const [page, setPage] = useState(1);
  const [activeFilter, setActiveFilter] = useState<"current" | "all">(
    "current"
  );

  const apiJobTypeFilter =
    activeFilter === "current" ? initialJobType : undefined;

  const {
    data: paginatedData,
    isFetching,
    refetch,
    isLoading,
    isError,
  } = useQuery({
    queryKey: [...queryKeys.admin.exportJobs.all, page, apiJobTypeFilter],
    queryFn: () => getExportJobs(page, apiJobTypeFilter),
    enabled: isOpen,
    placeholderData: (previousData) => previousData,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (Array.isArray(data?.results)) {
        const hasPendingJob = data.results.some(
          (job) => job.status === "Pending" || job.status === "In Progress"
        );
        return hasPendingJob ? 10000 : false;
      }
      return false;
    },
  });

  const handleTabChange = (value: string) => {
    setPage(1);
    setActiveFilter(value as "current" | "all");
  };

  const jobs = paginatedData?.results;
  const pageCount = paginatedData
    ? Math.ceil(paginatedData.count / PAGE_SIZE)
    : 0;

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-5xl h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>سجل طلبات التصدير</DialogTitle>
          <DialogDescription>
            تتبع حالة طلبات تصدير البيانات. يمكنك التبديل بين عرض هذا النوع فقط
            أو عرض الكل.
          </DialogDescription>
        </DialogHeader>

        <Tabs
          value={activeFilter}
          onValueChange={handleTabChange}
          className="mt-2"
        >
          <div className="flex justify-between items-center mb-4">
            <TabsList>
              <TabsTrigger value="current">هذا النوع</TabsTrigger>
              <TabsTrigger value="all">الكل</TabsTrigger>
            </TabsList>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              <RefreshCcw className="me-2 h-4 w-4" />
              تحديث
            </Button>
          </div>
        </Tabs>

        <div className="flex-1 overflow-auto pr-2">
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>تاريخ الإنشاء</TableHead>
                  <TableHead>المستخدم</TableHead>
                  <TableHead>الفلاتر</TableHead>
                  <TableHead>الحالة</TableHead>
                  <TableHead>المدة</TableHead>
                  <TableHead className="text-left">إجراءات</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell>
                        <Skeleton className="h-5 w-32" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-5 w-24" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-5 w-40" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-6 w-28 rounded-full" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-5 w-20" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-9 w-24" />
                      </TableCell>
                    </TableRow>
                  ))
                ) : isError ? (
                  <TableRow>
                    <TableCell
                      colSpan={6}
                      className="text-center text-destructive"
                    >
                      حدث خطأ أثناء تحميل قائمة المهام.
                    </TableCell>
                  </TableRow>
                ) : jobs && jobs.length > 0 ? (
                  jobs.map((job) => (
                    <TableRow key={job.id}>
                      <TableCell>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger className="cursor-default">
                              {formatDistanceToNow(new Date(job.created_at), {
                                addSuffix: true,
                                locale: ar,
                              })}
                            </TooltipTrigger>
                            <TooltipContent>
                              {formatDate(new Date(job.created_at), "PPPpp", {
                                locale: ar,
                              })}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </TableCell>
                      <TableCell>{job.requesting_user}</TableCell>
                      <TableCell>{formatJobFilters(job.filters)}</TableCell>
                      <TableCell>
                        <JobStatus
                          status={job.status}
                          errorMessage={job.error_message}
                        />
                      </TableCell>
                      <TableCell>
                        {formatJobDuration(job.created_at, job.completed_at)}
                      </TableCell>
                      <TableCell className="text-left">
                        {job.status === "Success" && job.file_url ? (
                          <Button asChild size="sm" variant="ghost">
                            <a
                              href={job.file_url}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <Download className="me-2 h-4 w-4" />
                              تحميل
                            </a>
                          </Button>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center">
                      لا توجد طلبات تصدير حتى الآن.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </div>

        <DataTablePagination
          page={page}
          pageCount={pageCount}
          setPage={setPage}
          canPreviousPage={!!paginatedData?.previous}
          canNextPage={!!paginatedData?.next}
          isFetching={isFetching}
        />
      </DialogContent>
    </Dialog>
  );
}
