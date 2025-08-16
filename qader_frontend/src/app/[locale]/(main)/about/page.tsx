// In your page.tsx (server component)
import { getAboutPageContent } from "@/services/content.service";
import AboutPageClient from "@/components/features/main/about/AboutPageClient";

const AboutPage = async () => {
  const data = await getAboutPageContent();
  return <AboutPageClient data={data} />;
};

export default AboutPage;
