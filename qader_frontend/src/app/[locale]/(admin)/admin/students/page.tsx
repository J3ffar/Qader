"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import StudentClient from "@/components/features/admin/students/StudentClient";
import AddStudentDialog from "@/components/features/admin/students/components/AddStudentDialog";
import { ExportControl } from "@/components/features/admin/shared/ExportControl";

export default function AdminStudentsPage() {
  const t = useTranslations("Admin.StudentManagement");
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
            <ExportControl exportType="users" roles={["student"]} />
            <Button onClick={() => setAddDialogOpen(true)}>
              <Plus className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
              {t("addUser")}
            </Button>
          </div>
        </div>
        <StudentClient />
      </div>

      <AddStudentDialog
        isOpen={isAddDialogOpen}
        onOpenChange={setAddDialogOpen}
      />
    </>
  );
}
