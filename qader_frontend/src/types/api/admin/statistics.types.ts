export interface PerformanceBySection {
  section_name: string;
  section_slug: string;
  average_accuracy: number | null;
  total_attempts: number;
}

export interface QuestionStat {
  id: number;
  question_text: string;
  attempt_count: number;
  accuracy_rate: number;
}

export interface DailyActivity {
  date: string; // "YYYY-MM-DD"
  questions_answered: number;
  tests_completed: number;
}

export interface AdminStatisticsOverview {
  total_active_students: number;
  new_registrations_period: number;
  total_questions_answered_period: number;
  total_tests_completed_period: number;
  overall_average_test_score: number | null;
  overall_average_accuracy: number | null;
  performance_by_section: PerformanceBySection[];
  most_attempted_questions: QuestionStat[];
  lowest_accuracy_questions: QuestionStat[];
  daily_activity: DailyActivity[];
}

export interface ExportTaskResponse {
  task_id: string;
  message: string;
  status_check_url: string | null;
}

export interface StatisticsOverviewParams {
  date_from?: string; // "YYYY-MM-DD"
  date_to?: string; // "YYYY-MM-DD"
}

export interface StatisticsExportParams extends StatisticsOverviewParams {
  format?: "csv" | "xlsx";
}
