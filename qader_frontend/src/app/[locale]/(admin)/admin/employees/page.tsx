"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import EmployeeClient from "@/components/features/admin/employees/EmployeeClient";
import AddEmployeeDialog from "@/components/features/admin/employees/components/AddEmployeeDialog";
import { ExportControl } from "@/components/features/admin/shared/ExportControl";

export default function AdminEmployeesPage() {
  const t = useTranslations("Admin.EmployeeManagement");
  const [isAddDialogOpen, setAddDialogOpen] = useState(false);

  return (
    <>
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
            <p className="text-muted-foreground">{t("description")}</p>
          </div>
          <div className="flex items-center gap-2">
            <ExportControl
              exportType="users"
              roles={["admin", "sub_admin", "teacher", "trainer"]}
            />
            <Button onClick={() => setAddDialogOpen(true)}>
              <Plus className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
              {t("addUser")}
            </Button>
          </div>
        </div>
        <EmployeeClient />
      </div>

      <AddEmployeeDialog
        isOpen={isAddDialogOpen}
        onOpenChange={setAddDialogOpen}
      />
    </>
  );
}
