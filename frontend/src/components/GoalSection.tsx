import { useEffect, useState } from "react";
import {
  acceptGoal, adjustGoalPlan, cancelGoal, createGoal, draftGoal, fetchGoal,
  fetchGoalTypes, fetchPlan, fetchProgress, goalErrorMessage, regenerateGoal, updatePlanDay,
} from "../api/goals";
import { addDays, todayISO } from "../dates";
import type { ExperienceLevel, Goal, GoalPayload, GoalPlanDay, GoalProgress, GoalTypeInfo, Workout } from "../types/goal";
import type { Metric } from "../types/metric";
import { Button } from "./Button";

type Props = { habitId: number; metrics: Metric[]; onChanged: () => Promise<void> };
type GoalChoice = "running_plan" | "frequency" | "metric_target";
type RaceType = "5k" | "10k" | "half_marathon" | "marathon";

export function GoalSection({ habitId, metrics, onChanged }: Props) {
  const [types, setTypes] = useState<GoalTypeInfo[]>([]);
  const [disclaimer, setDisclaimer] = useState("");
  const [goal, setGoal] = useState<Goal | null>(null);
  const [progress, setProgress] = useState<GoalProgress | null>(null);
  const [choice, setChoice] = useState<GoalChoice | null>(null);
  const [level, setLevel] = useState<ExperienceLevel>("beginner");
  const [raceType, setRaceType] = useState<RaceType>("5k");
  const [unit, setUnit] = useState<"mi" | "km">("mi");
  const [targetDate, setTargetDate] = useState("");
  const [frequency, setFrequency] = useState("");
  const [monthlyFrequency, setMonthlyFrequency] = useState("");
  const [period, setPeriod] = useState<"week" | "month" | "both">("week");
  const [metricId, setMetricId] = useState<number>(metrics.find((m) => m.type !== "boolean")?.id ?? 0);
  const [targetValue, setTargetValue] = useState("");
  const [startValue, setStartValue] = useState("");
  const [planSource, setPlanSource] = useState<"linear" | "ai" | "manual">("linear");
  const [draftPayload, setDraftPayload] = useState<GoalPayload | null>(null);
  const [draft, setDraft] = useState<GoalPlanDay[]>([]);
  const [plan, setPlan] = useState<Workout[]>([]);
  const [editPrompt, setEditPrompt] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const active = await fetchGoal(habitId);
    setGoal(active);
    setProgress(active ? await fetchProgress(habitId) : null);
    if (active?.goal_type === "metric_target") {
      const start = todayISO();
      const last = active.end_date && active.end_date < addDays(start, 30) ? active.end_date : addDays(start, 30);
      setPlan(await fetchPlan(habitId, start, last));
    } else setPlan([]);
  }

  useEffect(() => {
    fetchGoalTypes().then((r) => { setTypes(r.goal_types); setDisclaimer(r.disclaimer); }).catch(console.error);
    load().catch(console.error);
  }, [habitId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!metricId && metrics.some((m) => m.type !== "boolean")) {
      setMetricId(metrics.find((m) => m.type !== "boolean")!.id);
    }
  }, [metrics, metricId]);

  async function run(action: () => Promise<void>) {
    setError(null);
    try {
      await action();
      await load();
      setChoice(null);
      setDraft([]);
      setDraftPayload(null);
      await onChanged();
    } catch (err) {
      setError(goalErrorMessage(err));
    }
  }

  const raceLabel = (id: string) => types.find((t) => t.id === id)?.label ?? id;
  const metric = metrics.find((m) => m.id === metricId);
  const metricPayload: GoalPayload = {
    goal_type: "metric_target",
    metric_id: metricId,
    target_value: Number(targetValue),
    start_value: startValue === "" ? 0 : Number(startValue),
    target_date: targetDate,
    plan_source: planSource,
  };

  function makeManualPlan(): GoalPlanDay[] {
    const days: GoalPlanDay[] = [];
    for (let day = todayISO(); day <= targetDate; day = addDays(day, 1)) {
      days.push({ date: day, target_value: null, workout_type: "target" });
    }
    return days;
  }

  async function submitGoal(e: React.FormEvent) {
    e.preventDefault();
    if (choice === "running_plan") {
      await run(() => createGoal(habitId, { goal_type: "running_plan", race_type: raceType, target_date: targetDate, experience_level: level, unit }));
    } else if (choice === "frequency") {
      const count = Number(frequency);
      await run(() => createGoal(habitId, {
        goal_type: "frequency",
        ...(period !== "month" ? { per_week: count } : {}),
        ...(period !== "week" ? { per_month: period === "both" ? Number(monthlyFrequency) : count } : {}),
        target_date: targetDate || null,
      }));
    } else if (choice === "metric_target") {
      const payload = metricPayload;
      if (planSource === "linear") {
        await run(() => createGoal(habitId, payload));
      } else if (planSource === "ai") {
        setError(null);
        try {
          const response = await draftGoal(habitId, payload);
          setDraft(response.plan);
          setDraftPayload(payload);
          setDisclaimer(response.disclaimer);
        } catch (err) { setError(goalErrorMessage(err)); }
      } else {
        setDraft(makeManualPlan());
        setDraftPayload(payload);
      }
    }
  }

  function updateDraftDay(index: number, changes: Partial<GoalPlanDay>) {
    setDraft((items) => items.map((item, i) => i === index ? { ...item, ...changes } : item));
  }

  async function saveEditedDay(day: Workout, target: string, type: string) {
    await run(() => updatePlanDay(habitId, {
      date: day.date,
      target_value: type === "rest" ? null : target === "" ? null : Number(target),
      workout_type: type as GoalPlanDay["workout_type"],
      notes: day.notes,
    }));
  }

  return (
    <section>
      <h3>Goal</h3>
      {error && <p className="alert alert--error" role="alert">{error}</p>}
      {goal ? (
        <div className="card">
          {goal.goal_type === "frequency" ? (
            <>
              <strong>Frequency goal</strong>
              {goal.per_week != null && <p>{progress?.week_completed ?? 0} of {goal.per_week} days this week</p>}
              {goal.per_month != null && <p>{progress?.month_completed ?? 0} of {goal.per_month} days this month</p>}
              {goal.end_date && <p>Until {goal.end_date}</p>}
            </>
          ) : goal.goal_type === "metric_target" ? (
            <>
              <p><strong>{metric?.name ?? "Metric target"}:</strong> {goal.target_value} {goal.unit} by {goal.end_date ?? goal.target_date} — {progress?.status_label} ({progress?.metric_progress ?? 0}% complete)</p>
              <p className="muted"><small>General guidance, not medical advice.</small></p>
              <div className="form-row">
                <input className="input" aria-label="Adjust remaining plan" placeholder="Ask coach to adjust remaining plan" value={editPrompt} onChange={(e) => setEditPrompt(e.target.value)} />
                <Button onClick={() => void run(async () => { await adjustGoalPlan(habitId, editPrompt); setEditPrompt(""); })} disabled={!editPrompt.trim()}>Adjust plan</Button>
              </div>
              {plan.length > 0 && (
                <div className="goal-plan">
                  <h4>Edit upcoming targets</h4>
                  {plan.map((day) => (
                    <div className="form-row" key={day.date}>
                      <label>{day.date}</label>
                      <select className="input" aria-label={`Plan type ${day.date}`} defaultValue={day.workout_type} onChange={(e) => void saveEditedDay(day, String(day.target_value ?? ""), e.target.value)}>
                        <option value="target">Target</option><option value="rest">Rest</option><option value="deload">Deload</option>
                      </select>
                      <input className="input" type="number" min="0" step="any" aria-label={`Target ${day.date}`} defaultValue={day.target_value ?? ""} onBlur={(e) => void saveEditedDay(day, e.target.value, day.workout_type)} />
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <p><strong>{raceLabel(goal.race_type ?? goal.goal_type)}</strong> on {goal.target_date} ({goal.experience_level}) — {progress?.weeks_remaining} week(s) left, <strong>{progress?.status_label}</strong></p>
          )}
          {progress?.suggest_regenerate && <p className="alert alert--error">You're well behind plan. Regenerate the remaining plan?</p>}
          <div className="actions">
            {(goal.goal_type === "running_plan" || ["5k", "10k", "half_marathon", "marathon"].includes(goal.goal_type)) && <Button onClick={() => void run(() => regenerateGoal(habitId))}>Regenerate remaining plan</Button>}
            <Button variant="danger" onClick={() => void run(() => cancelGoal(habitId))}>Remove goal</Button>
          </div>
        </div>
      ) : choice === null ? (
        <Button variant="primary" onClick={() => setChoice("running_plan")}>+ Add goal</Button>
      ) : draftPayload ? (
        <div>
          <h4>Review plan draft</h4>
          {planSource === "ai" && <p className="muted"><small>{disclaimer || "General guidance, not medical advice."}</small></p>}
          <div className="goal-plan">
            {draft.map((day, index) => (
              <div className="form-row" key={day.date}>
                <label>{day.date}</label>
                <select className="input" aria-label={`Draft type ${day.date}`} value={day.workout_type} onChange={(e) => updateDraftDay(index, { workout_type: e.target.value as GoalPlanDay["workout_type"], target_value: e.target.value === "rest" ? null : day.target_value })}>
                  <option value="target">Target</option><option value="rest">Rest</option><option value="deload">Deload</option>
                </select>
                <input className="input" type="number" min="0" step="any" aria-label={`Draft target ${day.date}`} value={day.target_value ?? ""} disabled={day.workout_type === "rest"} onChange={(e) => updateDraftDay(index, { target_value: e.target.value === "" ? null : Number(e.target.value) })} />
              </div>
            ))}
          </div>
          <div className="actions">
            <Button variant="primary" onClick={() => draftPayload && void run(() => acceptGoal(habitId, draftPayload, draft))}>Accept plan</Button>
            <Button onClick={() => { setDraft([]); setDraftPayload(null); }}>Discard</Button>
          </div>
        </div>
      ) : (
        <div>
          <div className="actions">
            <Button onClick={() => setChoice("running_plan")}>Running plan</Button>
            <Button onClick={() => setChoice("frequency")}>Frequency goal</Button>
            <Button onClick={() => setChoice("metric_target")}>Metric target</Button>
          </div>
          <form className="form-row" onSubmit={submitGoal}>
            {choice === "running_plan" && (
              <>
                <label>Race <select className="input" value={raceType} onChange={(e) => setRaceType(e.target.value as RaceType)}>
                  {(["5k", "10k", "half_marathon", "marathon"] as RaceType[]).map((id) => <option key={id} value={id}>{raceLabel(id)}</option>)}
                </select></label>
                <label>Experience <select className="input" value={level} onChange={(e) => setLevel(e.target.value as ExperienceLevel)}>
                  <option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option>
                </select></label>
                <label>Units <select className="input" value={unit} onChange={(e) => setUnit(e.target.value as "mi" | "km")}><option value="mi">miles</option><option value="km">km</option></select></label>
                <label>Target date <input className="input" type="date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} required /></label>
                <Button variant="primary" type="submit">Create plan</Button>
              </>
            )}
            {choice === "frequency" && (
              <>
                <label>Times per period <input className="input" type="number" min="1" max="31" value={frequency} onChange={(e) => setFrequency(e.target.value)} required /></label>
                <label>Period <select className="input" value={period} onChange={(e) => setPeriod(e.target.value as typeof period)}>
                  <option value="week">Week</option><option value="month">Month</option><option value="both">Week and month</option>
                </select></label>
                {period === "both" && <label>Times per month <input className="input" type="number" min="1" max="31" value={monthlyFrequency} onChange={(e) => setMonthlyFrequency(e.target.value)} required /></label>}
                <label>End date (optional) <input className="input" type="date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} /></label>
                <Button variant="primary" type="submit">Create goal</Button>
              </>
            )}
            {choice === "metric_target" && (
              <>
                <label>Metric <select className="input" value={metricId || ""} onChange={(e) => setMetricId(Number(e.target.value))} required>
                  {metrics.filter((m) => m.type !== "boolean").map((m) => <option key={m.id} value={m.id}>{m.name}{m.unit ? ` (${m.unit})` : ""}</option>)}
                </select></label>
                <label>Target <input className="input" type="number" min="0.01" step="any" value={targetValue} onChange={(e) => setTargetValue(e.target.value)} required /></label>
                <label>Starting value (optional) <input className="input" type="number" min="0" step="any" value={startValue} onChange={(e) => setStartValue(e.target.value)} /></label>
                <label>End date <input className="input" type="date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} required /></label>
                <label>Plan mode <select className="input" value={planSource} onChange={(e) => setPlanSource(e.target.value as typeof planSource)}>
                  <option value="linear">Linear</option><option value="ai">AI coach</option><option value="manual">Manual</option>
                </select></label>
                <Button variant="primary" type="submit" disabled={!metrics.some((m) => m.type !== "boolean")}>Continue</Button>
              </>
            )}
          </form>
          <Button onClick={() => setChoice(null)}>Back</Button>
        </div>
      )}
      {disclaimer && choice === "running_plan" && <p className="muted"><small>{disclaimer}</small></p>}
    </section>
  );
}
