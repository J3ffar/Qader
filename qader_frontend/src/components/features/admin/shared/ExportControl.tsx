"use client";

import { useState } from "react";
import { Download, List } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ExportJobsDialog } from "@/components/features/admin/statistics/overview/ExportJobsDialog";
import { useCreateExportJob } from "@/hooks/useCreateExportJob";
import type {
  StatisticsExportParams,
  UserExportParams,
} from "@/types/api/admin/statistics.types";

type ExportType = "statistics" | "users";
type JobType = "TEST_ATTEMPTS" | "USERS";

interface ExportControlProps {
  exportType: "statistics" | "users";
  dateFilters?: Omit<StatisticsExportParams, "format">;
  roles?: string[]; // Add roles prop
}

// Helper to map our internal type to the API's type
const getJobTypeForApi = (exportType: "statistics" | "users"): JobType => {
  return exportType === "statistics" ? "TEST_ATTEMPTS" : "USERS";
};

export function ExportControl({
  exportType,
  dateFilters,
  roles,
}: ExportControlProps) {
  const [isJobsDialogOpen, setIsJobsDialogOpen] = useState(false);

  const { mutate: handleExport, isPending: isExporting } = useCreateExportJob({
    exportType,
    onSuccessCallback: () => setIsJobsDialogOpen(true),
  });

  const onExportClick = () => {
    let params: StatisticsExportParams | UserExportParams;

    if (exportType === "users") {
      params = { format: "xlsx" as const, role: roles };
    } else {
      params = { format: "xlsx" as const, ...dateFilters };
    }

    handleExport(params);
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <Button variant="outline" onClick={() => setIsJobsDialogOpen(true)}>
          <List className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
          سجل التصدير
        </Button>
        <Button onClick={onExportClick} disabled={isExporting}>
          <Download className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
          {isExporting ? "جاري التصدير..." : "تصدير"}
        </Button>
      </div>

      <ExportJobsDialog
        isOpen={isJobsDialogOpen}
        onOpenChange={setIsJobsDialogOpen}
        // Pass the correct initial filter to the dialog
        initialJobType={getJobTypeForApi(exportType)}
      />
    </>
  );
}
