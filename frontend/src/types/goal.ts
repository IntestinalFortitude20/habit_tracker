export type GoalType = "5k" | "10k" | "half_marathon" | "marathon" | "running_plan" | "frequency" | "metric_target";
export type ExperienceLevel = "beginner" | "intermediate" | "advanced";

export type GoalTypeInfo = { id: GoalType; label: string; distance_miles: number; min_weeks: Record<ExperienceLevel, number> };
export type GoalPlanDay = { date: string; target_value: number | null; workout_type: "target" | "rest" | "deload"; notes?: string | null };

export type PlanDayEdit = {
  target_value?: number | null;
  target_duration_min?: number | null;
  workout_type?: "rest" | "workout";
  notes?: string | null;
  confirm?: boolean;
};

export type Goal = {
  id: number;
  habit_id: number;
  metric_id: number | null;
  goal_type: GoalType;
  race_type: "5k" | "10k" | "half_marathon" | "marathon" | null;
  distance: number;
  unit: "mi" | "km";
  experience_level: ExperienceLevel;
  start_date: string;
  target_date: string;
  end_date: string | null;
  target_value: number | null;
  start_value: number | null;
  per_week: number | null;
  per_month: number | null;
  plan_source: "linear" | "ai" | "manual" | null;
  status: string;
};

export type Workout = {
  date: string;
  workout_type: string;
  target_distance: number | null;
  target_duration_min: number | null;
  target_value: number | null;
  phase: string | null;
  notes: string | null;
  edited: boolean;
  status: "rest" | "completed" | "missed" | "today" | "upcoming";
  entry_id: number | null;
  actual_distance: number | null;
  difference: number | null;
  percent_of_target: number | null;
};

export type GoalProgress = {
  goal: Goal;
  weeks_remaining: number;
  days_remaining: number;
  adherence: number | null;
  on_track: boolean;
  status_label: string;
  suggest_regenerate: boolean;
  week_completed?: number | null;
  week_target?: number | null;
  month_completed?: number | null;
  month_target?: number | null;
  metric_progress?: number | null;
};

export type GoalPayload = {
  goal_type: GoalType;
  target_date?: string | null;
  experience_level?: ExperienceLevel;
  start_date?: string;
  unit?: "mi" | "km";
  race_type?: "5k" | "10k" | "half_marathon" | "marathon";
  metric_id?: number;
  target_value?: number;
  start_value?: number;
  per_week?: number;
  per_month?: number;
  plan_source?: "linear" | "ai" | "manual";
};
