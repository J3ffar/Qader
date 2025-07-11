import { PATHS } from "@/constants/paths";
import { redirect } from "next/navigation";

// This page now only serves to redirect to the default community section.
export default function StudyCommunityRedirectPage() {
  // Assuming 'discussion' is the default view. Update PATHS accordingly.
  const locale = "ar"; // This would come from params in a real layout
  redirect(`/${locale}${PATHS.STUDY.COMMUNITY_DISCUSSION}`);
  // Return null or a loader as redirect() will throw an error to stop rendering.
  return null;
}
