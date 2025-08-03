import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  createExportJob,
  createUserExportJob,
} from "@/services/api/admin/statistics.service";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import type {
  StatisticsExportParams,
  UserExportParams,
} from "@/types/api/admin/statistics.types";

type ExportType = "statistics" | "users";
type ExportParams = StatisticsExportParams | UserExportParams; // Use a union type

interface UseCreateExportJobOptions {
  exportType: ExportType;
  onSuccessCallback?: () => void;
}

export const useCreateExportJob = ({
  exportType,
  onSuccessCallback,
}: UseCreateExportJobOptions) => {
  const queryClient = useQueryClient();

  const mutationFn = (params: ExportParams) => {
    switch (exportType) {
      case "users":
        return createUserExportJob(params as UserExportParams); // Cast to correct type
      case "statistics":
      default:
        return createExportJob(params as StatisticsExportParams); // Cast to correct type
    }
  };

  return useMutation({
    mutationFn,
    onSuccess: (data) => {
      toast.success(
        data.message || "تم استلام طلب التصدير الخاص بك وهو قيد المعالجة."
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.exportJobs.all,
      });
      onSuccessCallback?.();
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, "حدث خطأ غير متوقع."));
    },
  });
};
