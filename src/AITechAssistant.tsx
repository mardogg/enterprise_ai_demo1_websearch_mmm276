import React, { useEffect, useMemo, useState } from "react";
import { generatePlan as genPlan, TroubleshootResult } from "./generatePlan";
import { searchYoutube as ytSearch, YTItem } from "./youtube";

// ---- Small UI helpers (Tailwind-only) ----
export function Card({ className = "", children, title, actions }: {
  className?: string;
  children: React.ReactNode;
  title?: string | React.ReactNode;
  actions?: React.ReactNode;
}) {
  return (
    <section
      className={[
        "rounded-2xl bg-white/5 shadow-xl ring-1 ring-white/10",
        "backdrop-blur supports-[backdrop-filter]:bg-white/5",
        "p-5 md:p-6",
        className,
      ].join(" ")}
      aria-label={typeof title === "string" ? title : undefined}
    >
      {(title || actions) && (
        <header className="mb-4 flex items-center justify-between">
          {title ? (
            <h3 className="text-base font-semibold tracking-tight text-white">
              {title}
            </h3>
          ) : <div />}
          {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
        </header>
      )}
      {children}
    </section>
  );
}

export function Labeled({ id, label, hint, children }: {
  id: string;
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="text-sm font-medium text-slate-200">
        {label}
      </label>
      {hint && <p className="text-xs text-slate-400">{hint}</p>}
      {children}
    </div>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  const { className = "", ...rest } = props;
  return (
    <input
      className={[
        "w-full rounded-xl border-0 bg-white/5 px-3.5 py-2.5 text-white shadow-inner outline-none",
        "ring-1 ring-inset ring-white/10 placeholder:text-slate-400",
        "focus:ring-2 focus:ring-emerald-400/80",
        className,
      ].join(" ")}
      {...rest}
    />
  );
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const { className = "", ...rest } = props;
  return (
    <textarea
      className={[
        "w-full min-h-[88px] rounded-xl border-0 bg-white/5 px-3.5 py-2.5 text-white shadow-inner outline-none",
        "ring-1 ring-inset ring-white/10 placeholder:text-slate-400",
        "focus:ring-2 focus:ring-emerald-400/80",
        className,
      ].join(" ")}
      {...rest}
    />
  );
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  const { className = "", children, ...rest } = props;
  return (
    <select
      className={[
        "w-full rounded-xl border-0 bg-white/5 px-3.5 py-2.5 text-white shadow-inner outline-none",
        "ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-emerald-400/80",
        className,
      ].join(" ")}
      {...rest}
    >
      {children}
    </select>
  );
}

export function YouTubePlayer({ videoId, title }: { videoId?: string; title?: string }) {
  if (!videoId) return null;
  return (
    <div className="relative w-full overflow-hidden rounded-xl ring-1 ring-white/10" aria-label={title || "Tutorial video"}>
      <div className="pt-[56.25%]" />
      <iframe
        title={title || "Tutorial"}
        className="absolute left-0 top-0 h-full w-full"
        src={`https://www.youtube.com/embed/${videoId}`}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    </div>
  );
}

// ---- Domain contracts ----
type Observation = { text: string; checked: boolean };
export type Plan = {
  observations: Observation[];
  hypothesis: string;
  actionPlan: string[];
  escalationCriteria: string[];
  warnings?: string[];
};

// ---- Stubs (replace with API calls) ----
// remove local stubs; use external modules for plan and YouTube search

// ---- Main component ----
const productTypes = [
  "Laptop/PC",
  "Smartphone",
  "Tablet",
  "Router/Modem",
  "Game Console",
  "Printer",
  "Smart TV",
  "Other",
];

function formatPlanText(plan: Plan): string {
  const obs = plan.observations.map((o, i) => `- ${o.text}`).join("\n");
  const act = plan.actionPlan.map((s, i) => `${i + 1}. ${s}`).join("\n");
  const esc = plan.escalationCriteria.map((s) => `- ${s}`).join("\n");
  const warn = (plan.warnings || []).map((s) => `- ${s}`).join("\n");
  return [
    `## Observations`,
    obs,
    `\n## Hypothesis`,
    plan.hypothesis,
    `\n## Action Plan`,
    act,
    `\n## When to Escalate`,
    esc,
    warn ? `\n## Warnings\n${warn}` : "",
  ].join("\n");
}

export default function AITechAssistant() {
  // Form state
  const [productType, setProductType] = useState("");
  const [customType, setCustomType] = useState("");
  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");
  const [issue, setIssue] = useState("");
  const [details, setDetails] = useState("");

  // Derived
  const effectiveType = useMemo(() => (productType === "Other" ? (customType || "Other") : productType), [productType, customType]);
  const canGenerate = useMemo(() => [effectiveType, brand, model, issue].every(Boolean), [effectiveType, brand, model, issue]);

  // Plan state
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [copyMsg, setCopyMsg] = useState<string>("");

  // YouTube state
  const [videos, setVideos] = useState<YTItem[]>([]);
  const [currentVideoId, setCurrentVideoId] = useState<string | undefined>(undefined);

  // Diagnostics
  const [consent, setConsent] = useState(false);
  const [diagLoading, setDiagLoading] = useState(false);
  const [diagError, setDiagError] = useState<string | null>(null);
  const [diagSummary, setDiagSummary] = useState<string | null>(null);

  // Auto-generate when the required fields are filled
  useEffect(() => {
    let abort = false;
    async function run() {
      if (!canGenerate) return;
      setLoading(true);
      try {
        const r: TroubleshootResult = await genPlan(effectiveType, brand, model, issue, details);
        if (abort) return;
        const p: Plan = {
          observations: r.observations.map((t) => ({ text: t, checked: false })),
          hypothesis: r.hypothesis,
          actionPlan: r.actionPlan,
          escalationCriteria: r.escalationCriteria,
          warnings: r.warnings,
        };
        setPlan(p);
        // observations checkbox state must be preserved as objects; keep as-is from p
        const keywords = (r.suggestedKeywords || []).join(' ');
        const query = `${effectiveType} ${brand} ${model} ${issue} fix troubleshoot repair ${keywords}`.trim();
        const yt = await ytSearch(query);
        if (abort) return;
        setVideos(yt);
        setCurrentVideoId(yt[0]?.videoId);
      } finally {
        if (!abort) setLoading(false);
      }
    }
    run();
    return () => {
      abort = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canGenerate, productType, brand, model, issue, details]);

  function updateObservation(idx: number, checked: boolean) {
    setPlan((prev) => {
      if (!prev) return prev;
      const next = { ...prev, observations: prev.observations.map((o, i) => (i === idx ? { ...o, checked } : o)) };
      return next;
    });
  }

  async function copyPlan() {
    if (!plan) return;
    const obs = plan.observations
      .map((o) => `- [${o.checked ? "x" : " "}] ${o.text}`)
      .join("\n");
    const act = plan.actionPlan.map((s, i) => `${i + 1}. ${s}`).join("\n");
    const esc = plan.escalationCriteria.map((s) => `- ${s}`).join("\n");
    const warn = (plan.warnings || []).map((s) => `- ${s}`).join("\n");
    const text = [
      `## Observations`,
      obs,
      `\n## Hypothesis`,
      plan.hypothesis,
      `\n## Action Plan`,
      act,
      `\n## When to Escalate`,
      esc,
      warn ? `\n## Warnings\n${warn}` : "",
    ].join("\n");
    await navigator.clipboard.writeText(text);
    setCopyMsg("Plan copied");
    setTimeout(() => setCopyMsg(""), 2000);
  }

  function resetAll() {
    setProductType("");
    setBrand("");
    setModel("");
    setIssue("");
    setDetails("");
    setPlan(null);
    setVideos([]);
    setCurrentVideoId(undefined);
    setCopyMsg("");
    setConsent(false);
    setDiagLoading(false);
    setDiagError(null);
    setDiagSummary(null);
  }

  const planActions = (
    <div className="flex gap-2">
      <button
        type="button"
        onClick={copyPlan}
        className="inline-flex items-center rounded-xl bg-emerald-500 px-3 py-2 text-sm font-semibold text-emerald-950 shadow hover:bg-emerald-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300"
        aria-label="Copy troubleshooting plan"
      >
        Copy Plan
      </button>
      <button
        type="button"
        onClick={resetAll}
        className="inline-flex items-center rounded-xl bg-white/10 px-3 py-2 text-sm font-semibold text-white shadow hover:bg-white/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
        aria-label="Start over"
      >
        Start Over
      </button>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-950/98 p-4 text-slate-100 md:p-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">AI Tech Assistant</h1>
          <p className="mt-1 text-sm text-slate-400">Enter your device and issue on the left. Your plan and tutorial appear on the right.</p>
        </header>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6">
          {/* Left column */}
          <div className="space-y-4">
            <Card title="Step 1 — Identify Device">
              <div className="grid grid-cols-1 gap-4">
                <Labeled id="productType" label="Product Type" hint="Required">
                  <Select id="productType" value={productType} onChange={(e) => setProductType(e.target.value)}>
                    <option value="" disabled>
                      Select a type
                    </option>
                    {productTypes.map((t) => (
                      <option key={t} value={t} className="bg-slate-900">
                        {t}
                      </option>
                    ))}
                  </Select>
                </Labeled>
                {productType === "Other" && (
                  <Labeled id="customType" label="Specify type" hint="Describe your device type">
                    <Input id="customType" placeholder="e.g., VR headset, NAS, Smart speaker" value={customType} onChange={(e) => setCustomType(e.target.value)} />
                  </Labeled>
                )}
                <Labeled id="brand" label="Brand" hint="Required">
                  <Input id="brand" placeholder="Dell, Apple, Netgear…" value={brand} onChange={(e) => setBrand(e.target.value)} />
                </Labeled>
                <Labeled id="model" label="Model" hint="Required">
                  <Input id="model" placeholder="XPS 13, iPhone 12, R7000…" value={model} onChange={(e) => setModel(e.target.value)} />
                </Labeled>
              </div>
            </Card>

            <Card title="Step 2 — Describe Issue">
              <div className="grid grid-cols-1 gap-4">
                <Labeled id="issue" label="Issue summary" hint="Required">
                  <Input id="issue" placeholder="Overheating, won't boot, slow Wi‑Fi…" value={issue} onChange={(e) => setIssue(e.target.value)} />
                </Labeled>
                <Labeled id="details" label="Advanced details (optional)" hint="Error messages, when it happens, what you've tried…">
                  <Textarea id="details" value={details} onChange={(e) => setDetails(e.target.value)} />
                </Labeled>
              </div>
            </Card>

            <Card title="Diagnostics (optional)">
              <div className="space-y-3">
                <label className="inline-flex items-center gap-2 text-sm text-slate-200">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-white/20 bg-white/10 text-emerald-400 focus:ring-emerald-400"
                    checked={consent}
                    onChange={(e) => setConsent(e.target.checked)}
                    aria-checked={consent}
                  />
                  Allow read-only demo diagnostics
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={!consent || diagLoading}
                    onClick={async () => {
                      setDiagError(null);
                      setDiagSummary(null);
                      if (!consent) return;
                      setDiagLoading(true);
                      try {
                        // Simulate latency and potential error
                        await new Promise((r) => setTimeout(r, 600));
                        // 1-in-12 chance to show an error demo
                        if (Math.random() < 1/12) {
                          throw new Error("Temporary diagnostics service issue. Try again.");
                        }
                        setDiagSummary(
                          [
                            "Network: Adapter detected, DNS reachable, ping stable.",
                            "Storage: Free space 48%, SMART OK.",
                            "Performance: CPU normal, no thermal throttling.",
                            "Connectivity: Gateway reachable, HTTPS handshake OK.",
                          ].join("\n")
                        );
                      } catch (e: any) {
                        setDiagError(e?.message || "Unexpected error running diagnostics.");
                      } finally {
                        setDiagLoading(false);
                      }
                    }}
                    className={[
                      "inline-flex items-center rounded-xl px-3 py-2 text-sm font-medium",
                      !consent || diagLoading ? "bg-white/10 text-white/50" : "bg-white/10 text-white hover:bg-white/20",
                    ].join(" ")}
                    aria-disabled={!consent || diagLoading}
                  >
                    {diagLoading ? "Running…" : "Run Diagnostics"}
                  </button>
                </div>
                <div
                  className="rounded-xl bg-white/5 p-3 text-sm text-slate-300 ring-1 ring-inset ring-white/10"
                  aria-live="polite"
                >
                  {!consent && (
                    <span className="text-slate-400">Diagnostics are disabled. Check the box, then click Run Diagnostics.</span>
                  )}
                  {consent && !diagLoading && !diagError && diagSummary && (
                    <ul className="list-disc space-y-1 pl-5">
                      {diagSummary.split("\n").map((line, i) => (
                        <li key={i}>{line}</li>
                      ))}
                    </ul>
                  )}
                  {consent && diagLoading && (
                    <span className="text-slate-400">Collecting system info…</span>
                  )}
                  {consent && !diagLoading && diagError && (
                    <div className="rounded-lg bg-rose-500/10 p-2 text-rose-200 ring-1 ring-inset ring-rose-500/20">{diagError}</div>
                  )}
                </div>
              </div>
            </Card>
          </div>

          {/* Right column */}
          <div className="space-y-4">
            <Card title="Plan" actions={planActions}>
              <div aria-live="polite" className="space-y-4">
                {loading && (
                  <div className="text-sm text-slate-400">Generating plan…</div>
                )}
                {!loading && !plan && (
                  <div className="text-sm text-slate-400">Fill in Product Type, Brand, Model, and Issue to generate a plan.</div>
                )}
                {!loading && plan && (
                  <div className="space-y-6">
                    <div>
                      <h4 className="mb-2 text-sm font-semibold text-slate-200">Observations</h4>
                      <ul className="space-y-2">
                        {plan.observations.map((o, i) => (
                          <li key={i} className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              className="h-4 w-4 rounded border-white/20 bg-white/10 text-emerald-400 focus:ring-emerald-400"
                              checked={o.checked}
                              onChange={(e) => updateObservation(i, e.target.checked)}
                              aria-label={`Observation ${i + 1}`}
                            />
                            <span className="text-sm text-slate-200">{o.text}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 className="mb-1 text-sm font-semibold text-slate-200">Hypothesis</h4>
                      <p className="text-sm leading-relaxed text-slate-300">{plan.hypothesis}</p>
                    </div>

                    <div>
                      <h4 className="mb-1 text-sm font-semibold text-slate-200">Action Plan</h4>
                      <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-300">
                        {plan.actionPlan.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ol>
                    </div>

                    <div>
                      <h4 className="mb-1 text-sm font-semibold text-slate-200">When to Escalate</h4>
                      <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
                        {plan.escalationCriteria.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    </div>

                    {plan.warnings && plan.warnings.length > 0 && (
                      <div>
                        <h4 className="mb-1 text-sm font-semibold text-amber-300">Warnings</h4>
                        <ul className="list-disc space-y-1 pl-5 text-sm text-amber-200">
                          {plan.warnings.map((s, i) => (
                            <li key={i}>{s}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {copyMsg && (
                      <div className="text-xs text-emerald-300" aria-live="polite">{copyMsg}</div>
                    )}
                  </div>
                )}
              </div>
            </Card>

            <Card title="YouTube Helper">
              <div className="space-y-3">
                <YouTubePlayer videoId={currentVideoId} title={videos.find(v => v.videoId === currentVideoId)?.title} />
                {videos.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {videos.slice(0, 3).map((v, idx) => (
                      <button
                        key={v.videoId}
                        type="button"
                        onClick={() => setCurrentVideoId(v.videoId)}
                        className={[
                          "rounded-xl px-3 py-2 text-sm font-medium",
                          currentVideoId === v.videoId
                            ? "bg-emerald-500 text-emerald-950 shadow"
                            : "bg-white/10 text-white hover:bg-white/20",
                        ].join(" ")}
                        aria-label={`Use video #${idx + 1}: ${v.title}`}
                      >
                        Video #{idx + 1}
                      </button>
                    ))}
                    {plan && (
                      <a
                        href={`https://www.youtube.com/results?search_query=${encodeURIComponent(`${effectiveType} ${brand} ${model} ${issue} fix troubleshoot repair`)}`}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded-xl bg-white/10 px-3 py-2 text-sm font-medium text-white ring-1 ring-white/10 hover:bg-white/20"
                      >
                        Open on YouTube
                      </a>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">Generate a plan to see tutorial suggestions.</p>
                )}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
