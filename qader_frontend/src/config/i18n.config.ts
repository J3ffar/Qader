import {
  getRequestConfig,
  GetRequestConfigParams,
  RequestConfig,
} from "next-intl/server";
import type { AbstractIntlMessages } from "next-intl";
import { notFound } from "next/navigation";

export const locales = ["en", "ar"];
export const defaultLocale: Locale = "ar";

export type Locale = (typeof locales)[number];

export default getRequestConfig(
  async ({ locale }: GetRequestConfigParams): Promise<RequestConfig> => {
    const resolvedLocale = locale ?? defaultLocale;
    if (!locales.includes(resolvedLocale as any)) notFound();

    let messages: AbstractIntlMessages;
    try {
      // Load individual study files concurrently
      const [
        studyPageMessages,
        determineLevelMessages,
        testsMessages,
        traditionalLearningMessages,
        statisticsMessages,
        conversationalLearningMessages,
        emergencyModeMessages,
        reviewMessages,
      ] = await Promise.all([
        import(`@/locales/${resolvedLocale}/study/StudyPage.json`),
        import(`@/locales/${resolvedLocale}/study/determineLevel.json`),
        import(`@/locales/${resolvedLocale}/study/tests.json`),
        import(`@/locales/${resolvedLocale}/study/traditionalLearning.json`),
        import(`@/locales/${resolvedLocale}/study/statistics.json`),
        import(`@/locales/${resolvedLocale}/study/conversationalLearning.json`),
        import(`@/locales/${resolvedLocale}/study/emergencyMode.json`),
        import(`@/locales/${resolvedLocale}/study/review.json`),
      ]);

      // Merge all study-related messages into a single "Study" namespace
      const studyNamespace = {
        ...studyPageMessages.default,
        ...determineLevelMessages.default,
        ...testsMessages.default,
        ...traditionalLearningMessages.default,
        ...statisticsMessages.default,
        ...conversationalLearningMessages.default,
        ...emergencyModeMessages.default,
        ...reviewMessages.default,
      };

      // Load other top-level namespaces
      const commonMessages = (
        await import(`@/locales/${resolvedLocale}/common.json`)
      ).default;
      const authMessages = (
        await import(`@/locales/${resolvedLocale}/auth.json`)
      ).default;
      const navMessages = (await import(`@/locales/${resolvedLocale}/nav.json`))
        .default;

      // Construct the final messages object
      messages = {
        Common: commonMessages,
        Auth: authMessages,
        Nav: navMessages,
        Study: studyNamespace,
      };
    } catch (error) {
      console.error(
        `Could not load messages for locale: ${resolvedLocale}`,
        error
      );
      notFound();
    }

    return {
      locale: resolvedLocale,
      messages,
    };
  }
);
