"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RequestList } from "./RequestList";
import { Users } from "lucide-react";

export function PartnerRequestsDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <Users className="me-2 h-4 w-4" />
          طلبات الزملاء
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>طلبات الزملاء</DialogTitle>
        </DialogHeader>
        <Tabs defaultValue="received" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="received">الطلبات الواردة</TabsTrigger>
            <TabsTrigger value="sent">الطلبات المرسلة</TabsTrigger>
          </TabsList>
          <TabsContent value="received" className="mt-4">
            <RequestList direction="received" />
          </TabsContent>
          <TabsContent value="sent" className="mt-4">
            <RequestList direction="sent" />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
