export type AuditAction = "training" | "freeze" | "holdout" | "export";
export type GuideState = {status?: string; training: boolean; holdout: boolean; frozen: boolean};

// The guide follows the persisted lifecycle. It cannot freeze or evaluate for the user.
export function auditGuide(state: GuideState): {step: number; action: AuditAction | null; title: string; description: string; label: string; evidence?: "training" | "holdout"} {
  if (state.status === "training" || state.status === "evaluating") return {step: state.status === "training" ? 1 : 3, action: null, title: "This attempt is running or was interrupted", description: "Its record stays in the attempt log. Inspect it before starting another attempt; no completed result is assumed.", label: "Inspect attempt history"};
  if (state.status === "holdout_failed") return {step: 3, action: state.frozen ? "export" : null, title: "The later-period check could not finish", description: "Read the recorded error below. This frozen attempt remains visible; it has no completed holdout result.", label: "Export this failed attempt", evidence: "training"};
  if (state.holdout && state.frozen && state.status === "evaluated") return {step: 4, action: "export", title: "Keep the evidence", description: "Read the after-cost result below, inspect a trade, then save a bundle another researcher can rerun.", label: "Download reproduction ZIP", evidence: "holdout"};
  if (state.frozen && state.status === "frozen") return {step: 3, action: "holdout", title: "Check the saved settings on the later period", description: "The settings are locked. This next calculation uses the later historical period. Those observations may already be known to you.", label: "Evaluate locked historical holdout", evidence: "training"};
  if (state.training && state.status === "trained") return {step: 2, action: "freeze", title: "Read training, then lock these settings", description: "Review the earlier-period results and sensitivity rows below. Freezing saves this exact configuration before you evaluate the later period.", label: "Freeze this configuration", evidence: "training"};
  if (state.frozen) return {step: 3, action: null, title: "Inspect this saved attempt", description: "Its current state cannot start another holdout check. The attempt log retains its status and any error.", label: "Inspect attempt history"};
  return {step: 1, action: "training", title: state.status === "training_failed" ? "Retry training as a new attempt" : "Start with the earlier period", description: "Check whether the selected wallet idea beats two simple comparisons after fees and delays. Start with the current setup; every calculation creates a visible attempt.", label: "Inspect training vs benchmarks"};
}

export function costVerdict(valid: boolean, gross: number | null, net: number | null): {title: string; detail: string} {
  if (!valid || gross == null || net == null || !Number.isFinite(gross) || !Number.isFinite(net)) return {title: "No usable performance result", detail: "Required observations or a valid execution result are missing. Inspect the quality flags and exclusions; a missing value is not zero."};
  if (gross > 0 && net <= 0) return {title: "Costs erase the observed gain", detail: "The idea gains before modeled costs, but does not gain after costs in this period."};
  if (net < 0) return {title: "The idea loses after costs in this period", detail: "The modeled portfolio ends below its starting value. Red means a negative research result, not an application error."};
  if (net === 0) return {title: "The idea breaks even after costs", detail: "A flat result in this period does not establish an advantage over the benchmarks."};
  return {title: "The idea gains after costs in this period", detail: "Compare both benchmarks, exposure and trading activity. A positive result alone does not establish alpha or future profitability."};
}
