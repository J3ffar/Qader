// NO "use client" directive here. This is a Server Component.
import PartnersClient from "@/components/features/main/partners/PartnersClient";
import { getPartnersPageContent } from "@/services/content.service";

// This is the main page component. It's async and runs on the server.
export default async function PartnersPage() {
  // Data is fetched only ONCE on the server when the page is requested.
  const data = await getPartnersPageContent();

  // The fetched data is passed as a prop to the client component,
  // which will then handle all the interactive parts.
  return <PartnersClient data={data} />;
}
