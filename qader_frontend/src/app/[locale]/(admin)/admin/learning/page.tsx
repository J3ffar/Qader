import { redirect } from "next/navigation";
import { PATHS } from "@/constants/paths";

export default function LearningManagementPage() {
  redirect(PATHS.ADMIN.LEARNING.QUESTIONS);
}
