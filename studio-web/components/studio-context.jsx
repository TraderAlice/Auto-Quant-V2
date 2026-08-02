"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { events, factor, replaySteps } from "@/lib/data";
import { coreFactorFrom, validateCoreSnapshot } from "@/lib/core-snapshot";
import { researchSubjectFromProject } from "@/lib/research-subject";

const StudioContext = createContext(null);
const unavailableFactor = {
  id: "source-unavailable",
  name: "Core evidence unavailable",
  version: "NO VERIFIED SOURCE",
  frameId: "no verified frame",
};

export function StudioProvider({ children }) {
  const [asOfIndex, setAsOfIndex] = useState(4);
  const [selectedEventId, setSelectedEventId] = useState(events[0].id);
  const [cohortA, setCohortA] = useState([events[0].id, events[3].id]);
  const [cohortB, setCohortB] = useState([events[1].id, events[2].id]);
  const [source, setSource] = useState({ mode: "loading", snapshot: null, error: null });
  const [demoEnabled, setDemoEnabled] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/studio/snapshot", { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("Local Core snapshot is unavailable");
        return validateCoreSnapshot(await response.json());
      })
      .then((snapshot) => setSource({ mode: "connected", snapshot, error: null }))
      .catch((error) => {
        if (error.name !== "AbortError") {
          setSource({ mode: "unavailable", snapshot: null, error: error.message });
        }
      });
    return () => controller.abort();
  }, [retryKey]);

  const connectedFactor = coreFactorFrom(source.snapshot);
  const activeFactor = demoEnabled ? factor : connectedFactor || unavailableFactor;
  const activeAsOf = demoEnabled
    ? replaySteps[asOfIndex]
    : source.snapshot?.generatedAt || null;
  const subject = useMemo(
    () => demoEnabled ? null : researchSubjectFromProject(source.snapshot?.projects?.[0]),
    [demoEnabled, source.snapshot],
  );

  const value = useMemo(
    () => ({
      factor: activeFactor,
      events,
      replaySteps,
      asOfIndex,
      asOf: activeAsOf,
      source,
      subject,
      demoEnabled,
      enableDemo: () => setDemoEnabled(true),
      returnToCore: () => setDemoEnabled(false),
      retryCore: () => {
        setSource({ mode: "loading", snapshot: null, error: null });
        setRetryKey((value) => value + 1);
      },
      selectedEventId,
      selectedEvent: events.find((event) => event.id === selectedEventId) || events[0],
      cohortA,
      cohortB,
      setSelectedEventId,
      setAsOfIndex,
      stepBackward: () => setAsOfIndex((index) => Math.max(0, index - 1)),
      stepForward: () => setAsOfIndex((index) => Math.min(replaySteps.length - 1, index + 1)),
      assignToCohort(eventId, cohort) {
        const add = (current) => (current.includes(eventId) ? current : [...current, eventId]);
        if (cohort === "A") {
          setCohortA(add);
          setCohortB((current) => current.filter((id) => id !== eventId));
        } else {
          setCohortB(add);
          setCohortA((current) => current.filter((id) => id !== eventId));
        }
      },
      removeFromCohort(eventId) {
        setCohortA((current) => current.filter((id) => id !== eventId));
        setCohortB((current) => current.filter((id) => id !== eventId));
      },
    }),
    [activeAsOf, activeFactor, asOfIndex, selectedEventId, cohortA, cohortB, demoEnabled, source, subject],
  );

  return <StudioContext.Provider value={value}>{children}</StudioContext.Provider>;
}

export function useStudio() {
  const value = useContext(StudioContext);
  if (!value) throw new Error("useStudio must be used inside StudioProvider");
  return value;
}
