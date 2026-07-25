import { useState } from "react";

const SESSION_KEY = "es-rag-session-id";

function createSessionId(): string {
  return crypto.randomUUID();
}

export function useSession(): string {
  const [sessionId] = useState<string>(() => {
    const existing = localStorage.getItem(SESSION_KEY);
    if (existing) return existing;
    const created = createSessionId();
    localStorage.setItem(SESSION_KEY, created);
    return created;
  });
  return sessionId;
}
