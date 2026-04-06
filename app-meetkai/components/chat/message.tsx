"use client";

import { cn } from "@/lib/utils";
import { ToolResult } from "./tool-result";
import { Bot, User } from "lucide-react";
import type { UIMessage } from "ai";

interface ChatMessageProps {
  message: UIMessage;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  // Extract text content from parts (v6 API uses parts array)
  const textParts = message.parts.filter((p) => p.type === "text");
  // Extract tool parts (dynamic-tool or tool-* typed parts)
  const toolParts = message.parts.filter(
    (p) =>
      p.type === "dynamic-tool" ||
      (typeof p.type === "string" && p.type.startsWith("tool-")),
  );

  return (
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      <div
        className={cn(
          "w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0",
          isUser ? "bg-amber-dim" : "bg-bg-elevated",
        )}
      >
        {isUser ? (
          <User className="w-3.5 h-3.5 text-amber" />
        ) : (
          <Bot className="w-3.5 h-3.5 text-text-secondary" />
        )}
      </div>

      <div
        className={cn(
          "max-w-[85%] space-y-2",
          isUser ? "items-end" : "items-start",
          "flex flex-col",
        )}
      >
        {/* Text parts */}
        {textParts.map((part, i) => {
          const text = (part as { type: "text"; text: string }).text;
          if (!text) return null;
          return (
            <div
              key={i}
              className={cn(
                "px-3 py-2 rounded-lg text-sm",
                isUser
                  ? "bg-amber text-background rounded-tr-none"
                  : "bg-bg-elevated text-foreground rounded-tl-none",
              )}
            >
              <p className="whitespace-pre-wrap">{text}</p>
            </div>
          );
        })}

        {/* Tool invocation parts (v6: type is "dynamic-tool" or "tool-<name>") */}
        {toolParts.map((part, i) => {
          // Both DynamicToolUIPart and ToolUIPart shapes have toolName / type
          const p = part as {
            type: string;
            toolName?: string;
            toolCallId: string;
            state: string;
            input?: unknown;
            output?: unknown;
            errorText?: string;
          };

          const toolName =
            p.toolName ??
            (p.type.startsWith("tool-") ? p.type.slice(5) : p.type);

          if (p.state === "output-available" && p.output != null) {
            return (
              <ToolResult
                key={i}
                toolName={toolName}
                result={p.output as Record<string, unknown>}
              />
            );
          }

          if (p.state === "output-error") {
            return (
              <ToolResult
                key={i}
                toolName={toolName}
                result={{ error: p.errorText ?? "Tool error" }}
              />
            );
          }

          // input-streaming or input-available — show spinner
          return (
            <div
              key={i}
              className="flex items-center gap-2 px-3 py-2 bg-bg-elevated rounded-lg text-xs text-text-tertiary"
            >
              <span className="inline-block w-3 h-3 border border-text-tertiary border-t-transparent rounded-full animate-spin" />
              <span>Running {toolName}…</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
