export function visibleEvents(events, asOf) {
  const boundary = Date.parse(asOf);
  return events.filter((event) => Date.parse(event.availableAt) <= boundary);
}

export function hiddenEventSummary(events, asOf) {
  const boundary = Date.parse(asOf);
  return events.reduce(
    (summary, event) => {
      if (Date.parse(event.availableAt) <= boundary) return summary;
      const key = event.visibilityReason || "not-yet-available";
      summary.total += 1;
      summary.reasons[key] = (summary.reasons[key] || 0) + 1;
      return summary;
    },
    { total: 0, reasons: {} },
  );
}

export function cohortSummary(events, eventIds) {
  const selected = events.filter((event) => eventIds.includes(event.id));
  const adapters = selected.reduce((counts, event) => {
    counts[event.adapter] = (counts[event.adapter] || 0) + 1;
    return counts;
  }, {});
  const meanReaction = selected.length
    ? selected.reduce((sum, event) => sum + event.reaction, 0) / selected.length
    : 0;

  return {
    count: selected.length,
    meanReaction,
    adapters,
    tags: [...new Set(selected.flatMap((event) => event.tags))],
  };
}

export function compareCohorts(events, cohortA, cohortB) {
  const left = cohortSummary(events, cohortA);
  const right = cohortSummary(events, cohortB);
  return {
    left,
    right,
    reactionSpread: left.meanReaction - right.meanReaction,
    ready: left.count > 0 && right.count > 0,
  };
}

export function formatTime(value) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Shanghai",
  }).format(new Date(value));
}

export function formatPercent(value, digits = 2) {
  return `${new Intl.NumberFormat("zh-CN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
    signDisplay: "always",
  }).format(value)}%`;
}
