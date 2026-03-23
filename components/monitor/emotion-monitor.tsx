"use client";

import { motion } from "framer-motion";
import { Smile, AlertTriangle, Leaf, Moon, Sparkles, TrendingUp } from "lucide-react";
import { cn, EMOTION_COLORS } from "@/lib/utils";
import type { ReactorState, PerceptionData } from "@/lib/types";

interface EmotionMonitorProps {
  reactor: ReactorState | null;
  perception: PerceptionData | null;
  cameraRunning: boolean;
}

const flowerEmotionIcons = {
  BLOOM: Sparkles,
  ALERT: AlertTriangle,
  SOOTHE: Leaf,
  REST: Moon,
};

export function EmotionMonitor({
  reactor,
  perception,
  cameraRunning,
}: EmotionMonitorProps) {
  const emotionState = reactor?.flower_emotion || "REST";
  const colors = EMOTION_COLORS[emotionState] || EMOTION_COLORS.REST;
  const Icon = flowerEmotionIcons[emotionState] || Moon;

  // Get emotion scores from perception
  const emotionScores = perception?.vit_emotion?.scores || [];
  const emotionClasses = perception?.vit_emotion?.classes || [];
  const sortedEmotions = emotionClasses
    .map((cls, idx) => ({ emotion: cls, score: emotionScores[idx] || 0 }))
    .sort((a, b) => b.score - a.score);

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Smile className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium text-foreground">Emotion Analysis</span>
          </div>
          <span className="text-xs text-muted-foreground">
            {reactor?.source_model || "vit"}
          </span>
        </div>
      </div>

      {/* Flower Emotion State */}
      <div className="p-4">
        <div className={cn("rounded-lg p-4 transition-all", colors.bg, colors.glow)}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Icon className={cn("h-6 w-6", colors.text)} />
              <div>
                <span className={cn("text-lg font-bold", colors.text)}>
                  {emotionState}
                </span>
                <p className={cn("text-xs opacity-80", colors.text)}>
                  Source: {reactor?.source_emotion || "-"} (
                  {((reactor?.source_confidence || 0) * 100).toFixed(0)}%)
                </p>
              </div>
            </div>
            <div className="text-right">
              <span className={cn("text-2xl font-bold", colors.text)}>
                {((reactor?.stability || 0)).toFixed(0)}%
              </span>
              <p className={cn("text-xs opacity-80", colors.text)}>Stability</p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-3 h-2 w-full rounded-full bg-background/30 overflow-hidden">
            <motion.div
              className="h-2 bg-background/50"
              initial={{ width: 0 }}
              animate={{ width: `${reactor?.stability || 0}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>

        {!cameraRunning && (
          <p className="mt-3 text-center text-xs text-muted-foreground">
            Start camera to enable emotion tracking
          </p>
        )}
      </div>

      {/* Emotion Scores Table */}
      {cameraRunning && sortedEmotions.length > 0 && (
        <div className="border-t border-border p-4">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">
              Real-Time Scores
            </span>
            <TrendingUp className="h-3.5 w-3.5 text-muted-foreground" />
          </div>

          <div className="space-y-2">
            {sortedEmotions.slice(0, 7).map((item, idx) => {
              const percentage = Math.min(100, Math.max(0, item.score * 100));
              const isTop = idx === 0;

              return (
                <div key={item.emotion} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span
                      className={cn(
                        "capitalize",
                        isTop ? "font-medium text-primary" : "text-muted-foreground"
                      )}
                    >
                      {item.emotion}
                    </span>
                    <span
                      className={cn(
                        "font-mono",
                        isTop ? "text-primary" : "text-muted-foreground"
                      )}
                    >
                      {percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                    <motion.div
                      className={cn(
                        "h-1.5 rounded-full",
                        isTop ? "bg-primary" : "bg-muted-foreground/50"
                      )}
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
