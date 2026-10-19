export type GoalType = "5k" | "10k" | "half_marathon" | "marathon";
export type ExperienceLevel = "beginner" | "intermediate" | "advanced";

export type GoalTypeInfo = { id: GoalType; label: string; distance_miles: number; min_weeks: Record<ExperienceLevel, number> };

export type Goal = {
  id: number;
  habit_id: number;
  metric_id: number | null;
  goal_type: GoalType;
  distance: number;
  unit: "mi" | "km";
  experience_level: ExperienceLevel;
  start_date: string;
  target_date: string;
  status: string;
};

export type Workout = {
  date: string;
  workout_type: string;
  target_distance: number | null;
  target_duration_min: number | null;
  phase: string | null;
  notes: string | null;
  status: "rest" | "completed" | "missed" | "today" | "upcoming";
  entry_id: number | null;
  actual_distance: number | null;
  difference: number | null;
  percent_of_target: number | null;
};

export type GoalProgress = {
  goal: Goal;
  weeks_remaining: number;
  adherence: number | null;
  on_track: boolean;
  status_label: string;
  suggest_regenerate: boolean;
};

export type GoalPayload = {
  goal_type: GoalType;
  target_date: string;
  experience_level: ExperienceLevel;
  unit: "mi" | "km";
};
