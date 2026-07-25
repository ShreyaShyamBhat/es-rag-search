import type { Source, UploadResult } from "../types";

const API_BASE = "/api";

export async function uploadFile(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail || `Upload failed with status ${response.status}`);
  }

  return response.json();
}

export interface StreamQueryCallbacks {
  onToken: (token: string) => void;
  onSources: (sources: Source[]) => void;
  onDone: () => void;
  onError: (error: Error) => void;
}

export async function streamQuery(
  sessionId: string,
  question: string,
  callbacks: StreamQueryCallbacks,
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, question }),
    });

    if (!response.ok || !response.body) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(body.detail || `Query failed with status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const rawEvent of events) {
        if (!rawEvent.trim()) continue;
        const lines = rawEvent.split("\n");
        let eventName = "message";
        let data = "";
        for (const line of lines) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          else if (line.startsWith("data:")) data = line.slice(5).trim();
        }

        if (eventName === "sources") {
          callbacks.onSources(JSON.parse(data) as Source[]);
        } else if (eventName === "done") {
          callbacks.onDone();
        } else {
          callbacks.onToken(JSON.parse(data) as string);
        }
      }
    }
  } catch (error) {
    callbacks.onError(error instanceof Error ? error : new Error(String(error)));
  }
}
