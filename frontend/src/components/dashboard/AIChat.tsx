"use client";

import { useState, useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { chatWithAgent } from "@/lib/api";
import type { ChatMessage, PredictResponse, RecipeIngredient } from "@/lib/types";

interface Props {
  prediction: PredictResponse | null;
  recipe: RecipeIngredient[];
}

interface ErrorMessage {
  id: string;
  role: "system";
  content: string;
}

type UIMessage = ChatMessage | ErrorMessage;

export default function AIChat({ prediction, recipe }: Props) {
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Initialize with the static remediation analysis if it exists and we haven't started chatting yet
  useEffect(() => {
    if (prediction?.remediation && messages.length === 0) {
      setMessages([
        {
          role: "assistant",
          content: prediction.remediation.chemical_analysis,
          verified_adjustments: prediction.remediation.recipe_adjustments,
        }
      ]);
    }
  }, [prediction, messages.length]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      const scrollContainer = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages, isTyping]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !prediction || isTyping) return;

    const userMessage: ChatMessage = { role: "user", content: input.trim() };
    const chatHistory = messages.filter(m => m.role !== "system") as ChatMessage[];
    
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await chatWithAgent({
        message: userMessage.content,
        history: chatHistory,
        recipe: recipe.map(({ material, percentage }) => ({ material, percentage })),
        context: prediction
      });

      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: res.reply,
        verified_adjustments: res.verified_adjustments
      };

      // If there's a verification summary, prepend or append it to the message content,
      // or we can push it as part of the message state. The schema says ChatResponse has verification_summary,
      // but ChatMessage doesn't have it natively. Let's just append it to the content for display or
      // handle it inline if it exists. Actually, let's just append it to the content so it renders.
      if (res.verification_summary) {
        assistantMsg.content += `\n\n*Verification Summary: ${res.verification_summary}*`;
      }

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ErrorMessage = {
        id: crypto.randomUUID(),
        role: "system",
        content: `Error: ${err.message || "Failed to communicate with AI."}`
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full space-y-2">
      <h3 className="text-sm font-semibold text-[var(--ink)] shrink-0">AI Assistant</h3>
      
      <ScrollArea className="flex-1 min-h-0 bg-white/20 border border-[var(--ink-soft)]/20 rounded-xl p-3" ref={scrollRef}>
        <div className="space-y-4 pb-2 pr-4">
          {messages.length === 0 && !prediction && (
            <div className="text-[var(--ink-soft)] text-sm text-center italic mt-4">
              Awaiting data...
            </div>
          )}
          
          {messages.map((msg, i) => {
            if (msg.role === "system") {
              return (
                <div key={i} className="text-xs text-red-500 bg-red-500/10 p-2 rounded-lg text-center">
                  {msg.content}
                </div>
              );
            }

            const isUser = msg.role === "user";
            return (
              <div key={i} className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}>
                <div 
                  className={`text-sm px-3 py-2 rounded-2xl max-w-[90%] ${
                    isUser 
                      ? "bg-[var(--flower-petal)]/20 text-[var(--ink)] rounded-br-sm" 
                      : "bg-[var(--glaze-glass)] text-[var(--ink)] rounded-bl-sm border border-[var(--ink-soft)]/20"
                  }`}
                  style={{ whiteSpace: "pre-wrap" }}
                >
                  {msg.content}
                </div>

                {/* Render verified adjustments as inline cards */}
                {!isUser && msg.verified_adjustments && msg.verified_adjustments.length > 0 && (
                  <div className="mt-2 space-y-2 w-[90%]">
                    {msg.verified_adjustments.map((adj, idx) => (
                      <div key={idx} className="bg-[var(--ink-soft)]/5 border border-[var(--ink-soft)]/10 rounded-lg p-2 space-y-1">
                        <div className="flex items-center gap-2 text-sm">
                          <span className={`inline-block w-2 h-2 rounded-full ${
                            adj.action === "increase" || adj.action === "introduce"
                              ? "bg-green-500" : "bg-red-500"
                          }`} />
                          <span className="text-[var(--ink)] font-medium">{adj.material}</span>
                          <span className="text-[var(--ink-soft)] font-mono">
                            {adj.action === "increase" ? "+" : adj.action === "decrease" ? "" : "→"}
                            {adj.delta_percentage}%
                          </span>
                          <span className="text-[10px] text-[var(--ink-soft)] italic">{adj.action}</span>
                          {adj.recommendation === "recommended" && (
                            <span className="text-[10px] text-green-600 font-bold ml-auto">VERIFIED</span>
                          )}
                          {adj.recommendation === "not_recommended" && (
                            <span className="text-[10px] text-red-600 font-bold ml-auto">NOT REC</span>
                          )}
                        </div>
                        {adj.verified_cte != null && (
                          <div className="text-[11px] text-[var(--ink-soft)] font-mono pl-5 flex flex-wrap gap-x-2">
                            <span>CTE: {adj.verified_cte.toFixed(2)}</span>
                            {adj.verified_surface && <span>· Surf: {adj.verified_surface}</span>}
                            {adj.verified_crazing_risk != null && (
                              <span>· Crazing: {(adj.verified_crazing_risk * 100).toFixed(0)}%</span>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
          
          {isTyping && (
            <div className="flex items-start">
              <div className="bg-[var(--glaze-glass)] text-[var(--ink)] text-sm px-4 py-2 rounded-2xl rounded-bl-sm border border-[var(--ink-soft)]/20 animate-pulse flex gap-1 items-center">
                <span className="w-1.5 h-1.5 bg-[var(--ink-soft)] rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                <span className="w-1.5 h-1.5 bg-[var(--ink-soft)] rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                <span className="w-1.5 h-1.5 bg-[var(--ink-soft)] rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <form onSubmit={handleSubmit} className="pt-2 shrink-0 flex gap-2">
        <Input 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={prediction ? "Ask about adjusting this recipe..." : "Run a prediction first"}
          disabled={!prediction || isTyping}
          className="flex-1 bg-white/40 border-[var(--ink-soft)]/30 text-[var(--ink)]"
        />
        <button 
          type="submit" 
          disabled={!prediction || isTyping || !input.trim()}
          className="bg-[var(--ink-soft)] text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-opacity"
        >
          Send
        </button>
      </form>
    </div>
  );
}
