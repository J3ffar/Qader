"use client";

import { useTranslations } from "next-intl";
import {
  Bell,
  ChevronDown,
  LogOut,
  Search,
  Settings,
  UserCircle,
} from "lucide-react";
import { useAuthCore } from "@/store/auth.store";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Input } from "@/components/ui/input";

const getInitials = (name: string | undefined | null): string => {
  if (!name) return "A";
  return name
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
};

const AdminHeader = () => {
  const t = useTranslations("Nav.AdminHeader");
  const { user, isAuthenticated } = useAuthCore();

  return (
    <header className="sticky top-0 z-30 flex h-20 w-full items-center justify-between border-b bg-background px-6">
      {/* Center - Search Bar */}
      <div className="relative w-full max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground rtl:right-3 rtl:left-auto" />
        <Input
          type="search"
          placeholder={t("searchPlaceholder")}
          className="w-full bg-muted pl-9 rtl:pr-9"
        />
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center">
          <Button variant="ghost" size="icon" className="relative rounded-full">
            <Bell className="h-6 w-6" />
            <span className="absolute right-2 top-2 h-2.5 w-2.5 rounded-full bg-red-500" />
            <span className="sr-only">Notifications</span>
          </Button>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="flex h-auto items-center gap-3 p-1"
            >
              <div className="relative">
                <Avatar className="h-12 w-12">
                  <AvatarImage
                    src={user?.profile_picture_url || ""}
                    alt={user?.full_name || "Admin"}
                  />
                  <AvatarFallback>
                    {getInitials(user?.full_name)}
                  </AvatarFallback>
                </Avatar>
                <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background bg-green-500" />
              </div>
              <div className="hidden flex-col items-start text-start md:flex">
                <span className="font-semibold">
                  {user?.full_name || "Admin User"}
                </span>
                <span className="text-sm text-muted-foreground">
                  {t("greeting")}
                </span>
              </div>
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="start" forceMount>
            <DropdownMenuLabel>{t("myAccount")}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <UserCircle className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
              <span>{t("profile")}</span>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
              <span>{t("settings")}</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive focus:bg-destructive/10 focus:text-destructive">
              <LogOut className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
              <span>{t("logout")}</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

export default AdminHeader;
