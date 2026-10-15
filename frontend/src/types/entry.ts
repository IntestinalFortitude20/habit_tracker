export type MetricValue = {
  id: number;
  metric_id: number;
  value: number;
};

export type Entry = {
  id: number;
  habit_id: number;
  date: string;
  completed: boolean;
  metric_values: MetricValue[];
};

export type EntryPayload = {
  date: string;
  completed: boolean;
  metric_values: { metric_id: number; value: number }[];
};

export type HabitStats = {
  current_streak: number;
  longest_streak: number;
  completion_rate_7d: number;
  completion_rate_30d: number;
  total_completed_days: number;
  total_logged_days: number;
};
