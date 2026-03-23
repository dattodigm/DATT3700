"use client";

import { useState, useRef } from "react";
import { Terminal, Send, Trash2 } from "lucide-react";
import { cn, parseOSCArgs } from "@/lib/utils";

interface RawOscPanelProps {
  deviceName: string;
  onSend: (address: string, args: (number | string)[]) => void;
  disabled?: boolean;
}

interface LogEntry {
  id: number;
  timestamp: Date;
  address: string;
  args: (number | string)[];
  direction: "out" | "in";
}

export function RawOscPanel({
  deviceName,
  onSend,
  disabled = false,
}: RawOscPanelProps) {
  const [address, setAddress] = useState("/info/self");
  const [args, setArgs] = useState("");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logIdRef = useRef(0);

  const handleSend = () => {
    if (!address.trim() || !address.startsWith("/")) return;

    const parsedArgs = parseOSCArgs(args);
    onSend(address.trim(), parsedArgs);

    // Add to logs
    const newLog: LogEntry = {
      id: ++logIdRef.current,
      timestamp: new Date(),
      address: address.trim(),
      args: parsedArgs,
      direction: "out",
    };
    setLogs((prev) => [newLog, ...prev].slice(0, 100));
  };

  const handleClear = () => {
    setLogs([]);
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <Terminal className="h-5 w-5 text-muted-foreground" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">Raw OSC Console</h3>
          <p className="text-xs text-muted-foreground">Send custom OSC messages to {deviceName}</p>
        </div>
      </div>

      {/* Input Form */}
      <div className="space-y-3">
        <div>
          <label className="mb-1.5 block text-xs text-muted-foreground">
            OSC Address
          </label>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="/address"
            className="w-full rounded-lg border border-border bg-input px-3 py-2 font-mono text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs text-muted-foreground">
            Arguments (comma separated)
          </label>
          <input
            type="text"
            value={args}
            onChange={(e) => setArgs(e.target.value)}
            placeholder="1, 255, hello"
            className="w-full rounded-lg border border-border bg-input px-3 py-2 font-mono text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <button
          onClick={handleSend}
          disabled={disabled || !address.trim() || !address.startsWith("/")}
          className={cn(
            "flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
            (disabled || !address.trim() || !address.startsWith("/")) &&
              "cursor-not-allowed opacity-50"
          )}
        >
          <Send className="h-4 w-4" />
          Send OSC Message
        </button>
      </div>

      {/* Quick Commands */}
      <div className="space-y-2">
        <span className="text-xs font-medium text-muted-foreground">Quick Commands</span>
        <div className="flex flex-wrap gap-2">
          {[
            { addr: "/info/self", args: "" },
            { addr: "/stop", args: "" },
            { addr: "/motor", args: "128" },
            { addr: "/motor", args: "-128" },
            { addr: "/motion", args: "1" },
            { addr: "/preset", args: "1" },
          ].map((cmd, i) => (
            <button
              key={i}
              onClick={() => {
                setAddress(cmd.addr);
                setArgs(cmd.args);
              }}
              className="rounded-md bg-muted px-2 py-1 font-mono text-xs text-muted-foreground transition-colors hover:bg-muted/80 hover:text-foreground"
            >
              {cmd.addr} {cmd.args}
            </button>
          ))}
        </div>
      </div>

      {/* Log Output */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">Message Log</span>
          <button
            onClick={handleClear}
            className="flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <Trash2 className="h-3 w-3" />
            Clear
          </button>
        </div>

        <div className="h-64 overflow-y-auto rounded-lg border border-border bg-muted/30 p-3 font-mono text-xs">
          {logs.length === 0 ? (
            <span className="text-muted-foreground">No messages yet...</span>
          ) : (
            <div className="space-y-1">
              {logs.map((log) => (
                <div key={log.id} className="flex items-start gap-2">
                  <span className="text-muted-foreground">{formatTime(log.timestamp)}</span>
                  <span
                    className={cn(
                      "px-1 rounded",
                      log.direction === "out"
                        ? "bg-primary/10 text-primary"
                        : "bg-accent/10 text-accent"
                    )}
                  >
                    {log.direction === "out" ? "OUT" : "IN"}
                  </span>
                  <span className="text-foreground">{log.address}</span>
                  {log.args.length > 0 && (
                    <span className="text-muted-foreground">
                      [{log.args.join(", ")}]
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
