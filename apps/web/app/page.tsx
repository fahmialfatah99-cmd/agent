"use client";

import { useState } from "react";
import { Bot, MessageSquare, Cpu, Wrench, Shield, Send, Terminal } from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"chat" | "agents" | "providers" | "tools">("chat");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([
    {
      role: "assistant",
      content: "Hello! I am Super Intelligent Agent. How can I assist you today?",
    },
  ]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/api/v1/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || `Server error (${res.status})`);
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.content || "No response" },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ Error: ${
            error instanceof Error ? error.message : "Failed to reach agent API"
          }. Pastikan backend di port 8000 sudah berjalan.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-100">
      <aside className="w-64 border-r border-slate-800 bg-slate-900/60 p-4 flex flex-col justify-between">
        <div className="space-y-6">
          <div className="flex items-center space-x-3 px-2">
            <Bot className="h-8 w-8 text-blue-400" />
            <div>
              <h1 className="font-bold text-lg leading-tight">Super Agent</h1>
              <p className="text-xs text-slate-400">Multi-Process AI Engine</p>
            </div>
          </div>

          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab("chat")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === "chat" ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800"
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              <span>Chat</span>
            </button>
            <button
              onClick={() => setActiveTab("agents")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === "agents" ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800"
              }`}
            >
              <Terminal className="h-4 w-4" />
              <span>Agents</span>
            </button>
            <button
              onClick={() => setActiveTab("providers")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === "providers" ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800"
              }`}
            >
              <Cpu className="h-4 w-4" />
              <span>Providers</span>
            </button>
            <button
              onClick={() => setActiveTab("tools")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === "tools" ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800"
              }`}
            >
              <Wrench className="h-4 w-4" />
              <span>Tools</span>
            </button>
          </nav>
        </div>

        <div className="p-3 bg-slate-800/40 rounded-lg border border-slate-800 flex items-center space-x-2">
          <Shield className="h-4 w-4 text-emerald-400" />
          <span className="text-xs text-slate-300">Core Engine: Active</span>
        </div>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden">
        {activeTab === "chat" && (
          <div className="flex-1 flex flex-col h-full">
            <header className="border-b border-slate-800 px-6 py-4 bg-slate-900/30">
              <h2 className="text-lg font-semibold">Agent Conversation</h2>
              <p className="text-xs text-slate-400">Interactive reasoning and task execution loop</p>
            </header>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-2xl rounded-xl px-4 py-3 text-sm ${
                      m.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-slate-900 border border-slate-800 text-slate-200"
                    }`}
                  >
                    {m.content}
                  </div>
                </div>
              ))}
            </div>

            <form onSubmit={handleSend} className="p-4 border-t border-slate-800 bg-slate-900/40">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type a message or instruction..."
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm flex items-center space-x-1 disabled:opacity-50"
                >
                  <Send className="h-4 w-4" />
                  <span>{loading ? "..." : ""}</span>
                </button>
              </div>
            </form>
          </div>
        )}

        {activeTab === "agents" && (
          <div className="p-6 space-y-4">
            <h2 className="text-xl font-bold">Agent Orchestration</h2>
            <div className="grid grid-cols-2 gap-4">
              {["Planner", "Reasoner", "Executor", "Reflector"].map((agent) => (
                <div key={agent} className="p-4 rounded-lg bg-slate-900 border border-slate-800">
                  <h3 className="font-semibold text-blue-400">{agent}</h3>
                  <p className="text-xs text-slate-400 mt-1">Status: Ready</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "providers" && (
          <div className="p-6 space-y-4">
            <h2 className="text-xl font-bold">Model Providers</h2>
            <div className="grid grid-cols-2 gap-4">
              {["OpenAI", "Anthropic", "Google Gemini", "Groq", "Ollama"].map((provider) => (
                <div key={provider} className="p-4 rounded-lg bg-slate-900 border border-slate-800">
                  <h3 className="font-semibold text-slate-200">{provider}</h3>
                  <p className="text-xs text-slate-400 mt-1">Configured in .env</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "tools" && (
          <div className="p-6 space-y-4">
            <h2 className="text-xl font-bold">Registered Tools</h2>
            <div className="grid grid-cols-2 gap-4">
              {["Web Search", "Code Execution", "File Operations", "API Caller"].map((tool) => (
                <div key={tool} className="p-4 rounded-lg bg-slate-900 border border-slate-800">
                  <h3 className="font-semibold text-slate-200">{tool}</h3>
                  <p className="text-xs text-slate-400 mt-1">State: Available</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
