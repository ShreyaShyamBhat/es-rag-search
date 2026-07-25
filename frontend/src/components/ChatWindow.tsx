import { useState } from "react";
import { Send } from "lucide-react";
import { useChatStream } from "../hooks/useChatStream";
import { useSession } from "../hooks/useSession";
import { FileUpload, UploadedFileBadge } from "./FileUpload";
import { MessageBubble } from "./MessageBubble";
import { SourcePanel } from "./SourcePanel";
import type { UploadResult } from "../types";

export function ChatWindow() {
  const sessionId = useSession();
  const { messages, sendMessage, isStreaming } = useChatStream(sessionId);
  const [uploadedFiles, setUploadedFiles] = useState<UploadResult[]>([]);
  const [question, setQuestion] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isStreaming) return;
    setQuestion("");
    void sendMessage(trimmed);
  };

  return (
    <div className="mx-auto flex h-screen max-w-3xl flex-col gap-4 p-4">
      <header>
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
          Document Q&A
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Upload PDFs, then ask questions about them.
        </p>
      </header>

      <FileUpload onUploaded={(result) => setUploadedFiles((prev) => [...prev, result])} />

      {uploadedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {uploadedFiles.map((f) => (
            <UploadedFileBadge key={f.doc_id} filename={f.filename} />
          ))}
        </div>
      )}

      <div className="flex-1 space-y-3 overflow-y-auto rounded-xl border border-slate-200 p-4 dark:border-slate-800">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400">No messages yet — ask a question below.</p>
        )}
        {messages.map((m) => (
          <div key={m.id} className="space-y-2">
            <MessageBubble message={m} />
            {m.role === "assistant" && m.sources && <SourcePanel sources={m.sources} />}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your documents…"
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
        />
        <button
          type="submit"
          disabled={isStreaming || !question.trim()}
          className="flex items-center gap-1 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
          Send
        </button>
      </form>
    </div>
  );
}
