export interface Source {
  chunk_id: string;
  filename: string;
  page_number: number;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isStreaming?: boolean;
}

export interface UploadResult {
  doc_id: string;
  filename: string;
  num_pages: number;
  num_chunks: number;
}
