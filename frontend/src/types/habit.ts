export type Habit = {
  id: number;
  user_id: number;
  name: string;
  description?: string | null;
  archived: boolean;
  created_at: string;
};

export type CreateHabitPayload = {
  user_id: number;
  name: string;
  description?: string;
  archived?: boolean;
};
