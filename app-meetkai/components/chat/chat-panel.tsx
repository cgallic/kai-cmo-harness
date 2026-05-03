"use client";

import { useState, useRef, useEffect, useCallback, FormEvent } from "react";
import { ChatMessage } from "./message";
import { cn } from "@/lib/utils";
import { MessageSquare, X, Send, Loader2 } from "lucide-react";
import { readUIMessageStream, generateId } from "ai";
import type { UIMessage } from "ai";

// ---------------------------------------------------------------------------
// Custom useChat hook - v6 compatible, no @ai-sdk/react required
// Uses readUIMessageStream to consume the UIMessageStream protocol that
// toUIMessageStreamResponse() emits on the server.
// ---------------------------------------------------------------------------
function useChat({ api }: { api: string }) {
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      // Build user message in v6 UIMessage shape
      const userMessage: UIMessage = {
        id: generateId(),
        role: "user",
        parts: [{ type: "text", text }],
      };

      const nextMessages = [...messages, userMessage];
      setMessages(nextMessages);
      setIsLoading(true);

      abortRef.current = new AbortController();

      try {
        const res = await fetch(api, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages: nextMessages }),
          signal: abortRef.current.signal,
        });

        if (!res.ok || !res.body) {
          throw new Error(`Chat API error: ${res.status}`);
        }

        // readUIMessageStream yields updated UIMessage snapshots as chunks arrive.
        // We feed it the raw response body (ReadableStream<Uint8Array>) via
        // processResponseStream inside DefaultChatTransport; here we use a minimal
        // manual approach: decode the SSE body and pass it through readUIMessageStream.
        const assistantId = generateId();
        const assistantMessage: UIMessage = {
          id: assistantId,
          role: "assistant",
          parts: [],
        };

        // Add assistant placeholder so user sees the bubble appear immediately
        setMessages([...nextMessages, { ...assistantMessage }]);

        // readUIMessageStream expects a ReadableStream<UIMessageChunk>.
        // The server uses toUIMessageStreamResponse() which emits the
        // x-vercel-ai-ui-message-stream SSE format. We need to parse it.
        // We do this by piping through a transform that decodes the SSE lines.
        const sseStream = parseUIMessageSSEStream(res.body);

        const messageStream = readUIMessageStream({
          message: assistantMessage,
          stream: sseStream,
        });

        for await (const updated of messageStream) {
          setMessages([...nextMessages, { ...updated }]);
        }
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") return;
        console.error("Chat error:", err);
      } finally {
        setIsLoading(false);
        abortRef.current = null;
      }
    },
    [api, messages, isLoading],
  );

  const handleSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      const text = input.trim();
      if (!text) return;
      setInput("");
      void sendMessage(text);
    },
    [input, sendMessage],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setInput(e.target.value);
    },
    [],
  );

  return { messages, input, handleInputChange, handleSubmit, isLoading };
}

// ---------------------------------------------------------------------------
// SSE → UIMessageChunk transform
// The server emits lines like:
//   data: <json>\n\n
// where each JSON object is a UIMessageChunk. We decode those and push them
// into a ReadableStream<UIMessageChunk> that readUIMessageStream can consume.
// ---------------------------------------------------------------------------
function parseUIMessageSSEStream(
  body: ReadableStream<Uint8Array>,
): ReadableStream<import("ai").UIMessageChunk> {
  const decoder = new TextDecoder();
  let buffer = "";

  return new ReadableStream({
    async start(controller) {
      const reader = body.getReader();
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data:")) continue;
            const json = trimmed.slice(5).trim();
            if (!json || json === "[DONE]") continue;
            try {
              const chunk = JSON.parse(json) as import("ai").UIMessageChunk;
              controller.enqueue(chunk);
            } catch {
              // skip malformed lines
            }
          }
        }
      } finally {
        controller.close();
        reader.releaseLock();
      }
    },
  });
}

// ---------------------------------------------------------------------------
// ChatPanel component
// ---------------------------------------------------------------------------
export function ChatPanel() {
  const [open, setOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, input, handleInputChange, handleSubmit, isLoading } =
    useChat({ api: "/api/chat" });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          "fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full flex items-center justify-center shadow-lg transition-colors",
          open
            ? "bg-card border border-border"
            : "bg-amber hover:bg-amber-light",
        )}
      >
        {open ? (
          <X className="w-5 h-5 text-foreground" />
        ) : (
          <MessageSquare className="w-5 h-5 text-background" />
        )}
      </button>

      {/* Chat panel */}
      <div
        className={cn(
          "fixed bottom-20 right-6 z-50 w-96 h-[600px] max-h-[80vh] bg-card border border-border rounded-lg shadow-2xl flex flex-col transition-all duration-200",
          open
            ? "opacity-100 scale-100 translate-y-0"
            : "opacity-0 scale-95 translate-y-4 pointer-events-none",
        )}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <div className="w-8 h-8 rounded-full bg-amber-dim flex items-center justify-center">
            <MessageSquare className="w-4 h-4 text-amber" />
          </div>
          <div>
            <p className="text-sm font-semibold">Kai</p>
            <p className="text-[10px] text-text-tertiary">Marketing operator</p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
          {/* Welcome message if no messages */}
          {messages.length === 0 && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-full bg-bg-elevated flex items-center justify-center flex-shrink-0">
                <MessageSquare className="w-3.5 h-3.5 text-text-secondary" />
              </div>
              <div className="bg-bg-elevated px-3 py-2 rounded-lg rounded-tl-none text-sm">
                <p>
                  Hey, I&apos;m Kai. Ask me to explain the score, draft a brief,
                  run an audit, or prepare proposals for the approval queue.
                </p>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {isLoading &&
            messages.length > 0 &&
            messages[messages.length - 1]?.role === "user" && (
              <div className="flex items-center gap-2 text-text-tertiary text-xs">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Thinking...</span>
              </div>
            )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-3 border-t border-border">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={handleInputChange}
              placeholder="Ask Kai for the next move..."
              className="flex-1 px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-text-tertiary focus:outline-none focus:border-amber transition-colors"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="p-2 bg-amber text-background rounded-lg hover:bg-amber-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
