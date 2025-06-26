import { useTranslations } from "next-intl";
import { Plus, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import EmployeeClient from "@/components/admin/employees/EmployeeClient";

export default function AdminEmployeesPage() {
  const t = useTranslations("Admin.EmployeeManagement");

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-muted-foreground">{t("description")}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline">
            <Upload className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
            {t("export")}
          </Button>
          <Button>
            <Plus className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
            {t("addUser")}
          </Button>
        </div>
      </div>

      {/* Main Content Rendered by Client Component */}
      <EmployeeClient />
    </div>
  );
}
