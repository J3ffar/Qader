// src/components/features/platform/support/SupportTicketListSkeleton.tsx
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table";

export function SupportTicketListSkeleton() {
  return (
    <Table>
      <TableBody>
        {Array.from({ length: 4 }).map((_, i) => (
          <TableRow key={i}>
            <TableCell>
              <Skeleton className="h-5 w-20" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-6 w-24 rounded-full" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-5 w-48" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-5 w-12" />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
