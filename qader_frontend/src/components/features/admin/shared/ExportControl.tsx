"use client";

import { useState } from "react";
import { Download, List } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ExportJobsDialog } from "@/components/features/admin/statistics/overview/ExportJobsDialog";
import { useCreateExportJob } from "@/hooks/useCreateExportJob";
import type { StatisticsExportParams } from "@/types/api/admin/statistics.types";

type ExportType = "statistics" | "users";

interface ExportControlProps {
  exportType: ExportType;
  // Filters are only needed for statistics export
  dateFilters?: Omit<StatisticsExportParams, "format">;
}

export function ExportControl({ exportType, dateFilters }: ExportControlProps) {
  const [isJobsDialogOpen, setIsJobsDialogOpen] = useState(false);

  const { mutate: handleExport, isPending: isExporting } = useCreateExportJob({
    exportType,
    onSuccessCallback: () => setIsJobsDialogOpen(true),
  });

  const onExportClick = () => {
    const params = {
      format: "xlsx" as const,
      ...dateFilters,
    };
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
      />
    </>
  );
}
