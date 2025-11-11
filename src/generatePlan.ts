export type TroubleshootResult = {
  productType: string;
  brand: string;
  model: string;
  issueSummary: string;
  observations: string[];
  hypothesis: string;
  probableCauses?: string[];
  actionPlan: string[];
  escalationCriteria: string[];
  warnings?: string[];
  suggestedKeywords: string[];
};

export async function generatePlan(
  productType: string,
  brand: string,
  model: string,
  issue: string,
  details?: string
): Promise<TroubleshootResult> {
  const lower = `${issue} ${details ?? ''}`.toLowerCase();

  const baseObs = [
    `${brand} ${model}`.trim() + (issue ? `: "${issue}"` : ''),
    `Device type: ${productType}`,
    details ? `Extra details provided` : `No extra details provided`,
  ];

  // Thermal/fan case
  if (/(fan|overheat|overheating|hot|thermal)/i.test(lower)) {
    return {
      productType, brand, model, issueSummary: issue,
      observations: baseObs,
      hypothesis: `Likely thermal management issue (dust buildup, failing fan, or aggressive background load).`,
      probableCauses: [
        'Dust in vents or heatsink',
        'Fan degradation or obstruction',
        'Background processes maintaining high CPU/GPU usage',
      ],
      actionPlan: [
        'Check air vents; ensure device on hard surface; remove obstructions.',
        'Open Task Manager/Activity Monitor; identify processes >30% CPU and quit non-essential tasks.',
        'Update BIOS/firmware and chipset/graphics drivers.',
        'Use compressed air on vents (device powered off); avoid direct fan spin with high pressure.',
        'Monitor temps with a safe tool; confirm idle temps < 50–60°C (typical).',
      ],
      escalationCriteria: [
        'Fans not spinning or abnormal noises persist',
        'Sustained throttling under light load',
        'Device shuts down from thermal protection repeatedly',
      ],
      warnings: [
        'Unplug power and avoid liquid cleaners; take ESD precautions.',
        'Do not disassemble if under warranty; contact vendor support.',
      ],
      suggestedKeywords: ['overheating', 'fan noise', 'thermal throttling', 'clean vents'],
    };
  }

  // Connectivity/Wi-Fi case
  if (/(wifi|wi-fi|network|internet|slow)/i.test(lower)) {
    return {
      productType, brand, model, issueSummary: issue,
      observations: baseObs,
      hypothesis: `Likely connectivity issue (driver/adapter settings, AP interference, DNS).`,
      probableCauses: [
        'Outdated or unstable Wi‑Fi driver',
        'AP channel congestion/interference',
        'Power management suspending the adapter',
        'Inefficient DNS resolution',
      ],
      actionPlan: [
        'Power cycle modem/router; reconnect SSID; test another network.',
        'Update/reinstall Wi‑Fi driver; disable power save on adapter.',
        'Switch router to a less congested channel/band (5GHz/6GHz if available).',
        'Set DNS to reliable providers (e.g., 1.1.1.1 / 8.8.8.8) and test latency.',
        'Run ping tests and speed tests; compare on wired vs wireless.',
      ],
      escalationCriteria: [
        'Adapter missing or repeatedly disconnects after driver reinstall',
        'All devices on network see similar faults',
        'Severe packet loss despite proximity to AP',
      ],
      warnings: [
        'Avoid factory reset of router unless backup exists.',
        'Follow organization policy before changing network settings.',
      ],
      suggestedKeywords: ['wifi dropping', 'network slow', 'dns fix', 'driver update'],
    };
  }

  // Generic safe plan
  return {
    productType, brand, model, issueSummary: issue,
    observations: baseObs,
    hypothesis: `Insufficient information; start with non-destructive, reversible checks.`,
    probableCauses: [
      'Software conflicts or outdated drivers',
      'Background tasks consuming resources',
      'Minor configuration inconsistencies',
    ],
    actionPlan: [
      'Reproduce issue; note exact messages or codes.',
      'Check updates for OS/drivers/firmware; apply pending patches.',
      'Clean boot / Safe Mode to rule out third‑party conflicts.',
      'Run vendor diagnostics or built‑in troubleshooters.',
    ],
    escalationCriteria: [
      'Persistent errors after clean boot and updates',
      'Hardware indicators or SMART failures',
      'Data risk or repeated crashes',
    ],
    warnings: [
      'Back up important files before major changes.',
      'Follow warranty rules; avoid opening sealed devices.',
    ],
    suggestedKeywords: ['troubleshoot', 'driver update', 'safe mode', 'diagnostic'],
  };
}
