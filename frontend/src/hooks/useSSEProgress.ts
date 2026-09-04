"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/services/api";

export interface SSETelemetryData {
  step_name: string;
  progress: number;
  vram_allocated_mb: number;
  message: string;
}

export function useSSEProgress(jobId: string | null) {
  const [telemetry, setTelemetry] = useState<SSETelemetryData | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) {
      setTelemetry(null);
      setLogs([]);
      setIsConnected(false);
      setIsCompleted(false);
      setError(null);
      return;
    }

    const sseUrl = api.getSSEUrl(jobId);
    const eventSource = new EventSource(sseUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    eventSource.onmessage = (e) => {
      try {
        const data: SSETelemetryData = JSON.parse(e.data);
        setTelemetry(data);
        setLogs((prev) => [
          ...prev,
          `[${new Date().toLocaleTimeString()}] ${data.step_name} (${Math.round(
            data.progress * 100
          )}%) — VRAM: ${data.vram_allocated_mb.toFixed(0)}MB ${data.message ? `• ${data.message}` : ""}`,
        ]);

        if (data.step_name === "COMPLETED") {
          setIsCompleted(true);
          eventSource.close();
        } else if (data.step_name === "FAILED") {
          setError(data.message || "Job execution failed");
          eventSource.close();
        }
      } catch (err) {
        console.error("Error parsing SSE data", err);
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [jobId]);

  return {
    telemetry,
    logs,
    isConnected,
    isCompleted,
    error,
  };
}
