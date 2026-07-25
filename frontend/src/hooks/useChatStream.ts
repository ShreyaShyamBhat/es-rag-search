import { useCallback, useState } from "react";
import { streamQuery } from "../api/client";
import type { ChatMessage } from "../types";

export function useChatStream(sessionId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(
    async (question: string) => {
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: question,
      };
      const assistantId = crypto.randomUUID();
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsStreaming(true);

      const updateAssistant = (updater: (msg: ChatMessage) => ChatMessage) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? updater(m) : m)),
        );
      };

      await streamQuery(sessionId, question, {
        onToken: (token) => {
          updateAssistant((m) => ({ ...m, content: m.content + token }));
        },
        onSources: (sources) => {
          updateAssistant((m) => ({ ...m, sources }));
        },
        onDone: () => {
          updateAssistant((m) => ({ ...m, isStreaming: false }));
          setIsStreaming(false);
        },
        onError: (error) => {
          updateAssistant((m) => ({
            ...m,
            content: m.content || `Error: ${error.message}`,
            isStreaming: false,
          }));
          setIsStreaming(false);
        },
      });
    },
    [sessionId],
  );

  return { messages, sendMessage, isStreaming };
}
