import { Fragment } from "react";
import clsx from "clsx";
import type { ChatMessage, Source } from "../types";
import { CitationBadge } from "./CitationBadge";

const CITATION_PATTERN = /\[Source (\d+)(?:,\s*p\.\d+)?\]/g;

function renderContentWithCitations(content: string, sources?: Source[]) {
  if (!sources || sources.length === 0) return content;

  const parts: (string | React.ReactNode)[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  CITATION_PATTERN.lastIndex = 0;
  while ((match = CITATION_PATTERN.exec(content)) !== null) {
    const sourceIndex = Number(match[1]);
    const source = sources[sourceIndex - 1];

    parts.push(content.slice(lastIndex, match.index));
    if (source) {
      parts.push(
        <CitationBadge key={`${match.index}-${sourceIndex}`} index={sourceIndex} source={source} />,
      );
    } else {
      parts.push(match[0]);
    }
    lastIndex = match.index + match[0].length;
  }
  parts.push(content.slice(lastIndex));

  return parts.map((part, i) => <Fragment key={i}>{part}</Fragment>);
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={clsx("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={clsx(
          "max-w-2xl whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm leading-relaxed",
          isUser
            ? "bg-indigo-600 text-white"
            : "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100",
        )}
      >
        {renderContentWithCitations(message.content, message.sources)}
        {message.isStreaming && (
          <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-current align-middle" />
        )}
      </div>
    </div>
  );
}
