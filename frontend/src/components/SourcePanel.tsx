import { FileText } from "lucide-react";
import type { Source } from "../types";
import { sourceAnchorId } from "./CitationBadge";

export function SourcePanel({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null;

  return (
    <div className="max-w-2xl rounded-xl border border-slate-200 bg-white p-3 text-xs dark:border-slate-700 dark:bg-slate-900">
      <p className="mb-2 font-medium text-slate-500 dark:text-slate-400">Sources</p>
      <ul className="space-y-2">
        {sources.map((source, i) => (
          <li
            key={source.chunk_id}
            id={sourceAnchorId(source.chunk_id)}
            className="scroll-mt-4 rounded-lg bg-slate-50 p-2 dark:bg-slate-800"
          >
            <div className="mb-1 flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
              <FileText className="h-3 w-3" />
              <span className="font-medium">
                Source {i + 1} · {source.filename}, p.{source.page_number}
              </span>
            </div>
            <mark className="rounded bg-yellow-200/70 px-0.5 leading-relaxed text-slate-800 dark:bg-yellow-500/30 dark:text-slate-100">
              {source.snippet}
            </mark>
          </li>
        ))}
      </ul>
    </div>
  );
}
