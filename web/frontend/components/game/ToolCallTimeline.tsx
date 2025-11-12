"use client";

import { useState, useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp, Timer, Wand2 } from "lucide-react";

export type ToolCallStatus = "running" | "success" | "error";

export interface ToolCallTimelineItem {
  id: string;
  name: string;
  status: ToolCallStatus;
  input: unknown;
  output?: unknown;
  startedAt: number;
  finishedAt?: number;
  error?: string;
}

interface ToolCallTimelineProps {
  calls: ToolCallTimelineItem[];
  className?: string;
}

const statusConfig: Record<
  ToolCallStatus,
  { label: string; badgeClass: string; description: string }
> = {
  running: {
    label: "执行中",
    badgeClass: "bg-amber-500/10 text-amber-500 border border-amber-500/40",
    description: "工具正在执行…",
  },
  success: {
    label: "已完成",
    badgeClass: "bg-emerald-500/10 text-emerald-500 border border-emerald-500/40",
    description: "工具执行成功",
  },
  error: {
    label: "错误",
    badgeClass: "bg-rose-500/10 text-rose-500 border border-rose-500/40",
    description: "工具执行失败",
  },
};

function formatTimestamp(timestamp: number | undefined) {
  if (!timestamp) return "";
  try {
    return new Date(timestamp).toLocaleTimeString();
  } catch {
    return "";
  }
}

function formatDuration(startedAt: number, finishedAt?: number) {
  if (!startedAt || !finishedAt) return null;
  const durationMs = Math.max(0, finishedAt - startedAt);
  if (durationMs < 1000) {
    return `${durationMs}ms`;
  }
  const seconds = durationMs / 1000;
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  return `${Math.round(seconds / 60)}m`;
}

function PayloadBlock({ title, data }: { title: string; data: unknown }) {
  if (data === undefined || data === null || data === "") {
    return null;
  }

  let formatted: string;

  if (typeof data === "string") {
    formatted = data;
  } else {
    try {
      formatted = JSON.stringify(data, null, 2);
    } catch {
      formatted = String(data);
    }
  }

  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-muted-foreground">{title}</p>
      <pre className="max-h-48 overflow-auto rounded-md bg-muted/40 p-3 text-xs leading-relaxed text-muted-foreground">
        {formatted}
      </pre>
    </div>
  );
}

function ToolCallCard({ call }: { call: ToolCallTimelineItem }) {
  const [expanded, setExpanded] = useState(call.status !== "success");
  const status = statusConfig[call.status];
  const startedAtLabel = useMemo(() => formatTimestamp(call.startedAt), [call.startedAt]);
  const finishedAtLabel = useMemo(() => formatTimestamp(call.finishedAt), [call.finishedAt]);
  const durationLabel = useMemo(
    () => (call.finishedAt ? formatDuration(call.startedAt, call.finishedAt) : null),
    [call.finishedAt, call.startedAt]
  );

  return (
    <div className="rounded-lg border border-border/60 bg-card/60 p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={cn("border", status.badgeClass)}>
              {status.label}
            </Badge>
            <span className="font-medium text-sm">{call.name}</span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{status.description}</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {startedAtLabel && <span title="开始时间">{startedAtLabel}</span>}
          {finishedAtLabel && <span title="结束时间">→ {finishedAtLabel}</span>}
          {durationLabel && (
            <span className="inline-flex items-center gap-1" title="耗时">
              <Timer className="h-3 w-3" />
              {durationLabel}
            </span>
          )}
        </div>
      </div>

      {(call.input !== undefined || call.output !== undefined || call.error) && (
        <div className="mt-3 space-y-3">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={() => setExpanded((prev) => !prev)}
          >
            <span className="mr-2">{expanded ? "折叠详情" : "展开详情"}</span>
            {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </Button>

          {expanded && (
            <div className="space-y-3">
              <PayloadBlock title="输入参数" data={call.input} />
              {call.output !== undefined && <PayloadBlock title="工具返回" data={call.output} />}
              {call.error && (
                <div className="rounded-md bg-rose-500/10 p-3 text-xs text-rose-500">
                  {call.error}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ToolCallTimeline({ calls, className }: ToolCallTimelineProps) {
  if (!calls || calls.length === 0) {
    return null;
  }

  return (
    <Card className={cn("flex h-full flex-col", className)}>
      <CardHeader className="space-y-2 pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Wand2 className="h-5 w-5 text-primary" />
          工具调用追踪
        </CardTitle>
        <CardDescription>实时显示 DM 工具调用的输入、输出与耗时</CardDescription>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full">
          <div className="space-y-3 p-4">
            {calls.map((call) => (
              <ToolCallCard key={call.id} call={call} />
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

