import type { Source } from "../types";

interface CitationBadgeProps {
  index: number;
  source: Source;
}

export function sourceAnchorId(chunkId: string): string {
  return `source-${chunkId}`;
}

export function CitationBadge({ index, source }: CitationBadgeProps) {
  return (
    <a
      href={`#${sourceAnchorId(source.chunk_id)}`}
      title={source.snippet}
      className="mx-0.5 inline-flex items-center rounded bg-indigo-100 px-1.5 py-0.5 text-xs font-medium text-indigo-700 no-underline hover:bg-indigo-200 dark:bg-indigo-900/50 dark:text-indigo-300 dark:hover:bg-indigo-900"
    >
      Source {index}, p.{source.page_number}
    </a>
  );
}
