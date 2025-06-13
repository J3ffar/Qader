import {
  HydrationBoundary,
  QueryClient,
  dehydrate,
} from "@tanstack/react-query";

import { getTestAttemptDetails } from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import TraditionalLearningSession from "@/components/features/platform/study/traditional-learning/TraditionalLearningSession";

// Updated interface to match Next.js 15+ requirements
interface TraditionalPracticePageProps {
  params: Promise<{
    attemptId: string;
    locale: string; // Don't forget the locale param from your route structure
  }>;
}

export default async function TraditionalPracticePage({
  params,
}: TraditionalPracticePageProps) {
  // Await the params Promise
  const { attemptId } = await params;

  const queryClient = new QueryClient();

  // Prefetching data on the server for an instant load experience on the client.
  await queryClient.prefetchQuery({
    queryKey: [QUERY_KEYS.USER_TEST_ATTEMPT_DETAIL, attemptId],
    queryFn: () => getTestAttemptDetails(attemptId),
  });

  return (
    // HydrationBoundary passes the server-fetched data to the client,
    // avoiding a client-side fetch waterfall and showing the content immediately.
    <HydrationBoundary state={dehydrate(queryClient)}>
      <TraditionalLearningSession attemptId={attemptId} />
    </HydrationBoundary>
  );
}
