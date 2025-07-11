// This is the Server Component. It only fetches data.
import FaqClient from "@/components/features/main/questions/FaqClient";
import { getFaqPageContent } from "@/services/content.service";

export default async function QuestionsPage() {
  // Data is fetched once on the server when the page is requested.
  const data = await getFaqPageContent();

  // The fetched data is passed as a prop to the client component.
  return <FaqClient data={data} />;
}
