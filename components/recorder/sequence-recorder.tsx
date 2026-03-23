"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Circle,
  Square,
  Play,
  Pause,
  Save,
  FolderOpen,
  Tag,
  Clock,
  Activity,
  Trash2,
} from "lucide-react";
import { cn, formatTime } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
import type { SequenceEvent, MotionSequence } from "@/lib/types";

interface SequenceRecorderProps {
  onSave: (sequence: MotionSequence) => Promise<void>;
  onLoad: (name: string) => Promise<MotionSequence | null>;
  onPlay: (sequence: MotionSequence) => void;
  availableSequences: { label: string; name: string }[];
}

export function SequenceRecorder({
  onSave,
  onLoad,
  onPlay,
  availableSequences,
}: SequenceRecorderProps) {
  const {
    isRecording,
    recordStartTime,
    recordedEvents,
    currentSequenceLabel,
    currentSequenceName,
    loadedSequence,
    isPlaying,
    playbackProgress,
    startRecording,
    stopRecording,
    setSequenceLabel,
    setSequenceName,
    loadSequence,
    startPlayback,
    stopPlayback,
  } = useAppStore();

  const [elapsedTime, setElapsedTime] = useState(0);
  const [showLoadDialog, setShowLoadDialog] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Update elapsed time during recording
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setElapsedTime(Date.now() - recordStartTime);
      }, 100);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      setElapsedTime(0);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording, recordStartTime]);

  const handleStartRecording = () => {
    startRecording();
  };

  const handleStopRecording = () => {
    const events = stopRecording();
    // Events are still in the store
  };

  const handleSave = async () => {
    if (!currentSequenceLabel.trim() || !currentSequenceName.trim()) return;
    if (recordedEvents.length === 0) return;

    const sequence: MotionSequence = {
      label: currentSequenceLabel.trim(),
      name: currentSequenceName.trim(),
      duration: recordedEvents.length > 0
        ? recordedEvents[recordedEvents.length - 1].timestamp
        : 0,
      events: recordedEvents,
      created_at: new Date().toISOString(),
    };

    await onSave(sequence);
    loadSequence(sequence);
  };

  const handleLoad = async (name: string) => {
    const sequence = await onLoad(name);
    if (sequence) {
      loadSequence(sequence);
      setSequenceLabel(sequence.label);
      setSequenceName(sequence.name);
    }
    setShowLoadDialog(false);
  };

  const handlePlay = () => {
    if (loadedSequence) {
      startPlayback();
      onPlay(loadedSequence);
    }
  };

  const handleStop = () => {
    stopPlayback();
  };

  // Group sequences by label
  const groupedSequences = availableSequences.reduce(
    (acc, seq) => {
      if (!acc[seq.label]) acc[seq.label] = [];
      acc[seq.label].push(seq.name);
      return acc;
    },
    {} as Record<string, string[]>
  );

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium text-foreground">
              Sequence Recorder
            </span>
          </div>
          {isRecording && (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse-recording" />
              <span className="font-mono text-xs text-red-400">
                {formatTime(elapsedTime)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Labels & Name */}
      <div className="p-4 space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1.5 block text-xs text-muted-foreground">
              <Tag className="mr-1 inline h-3 w-3" />
              Emotion Label
            </label>
            <input
              type="text"
              value={currentSequenceLabel}
              onChange={(e) => setSequenceLabel(e.target.value)}
              placeholder="e.g., calm, happy, alert"
              disabled={isRecording}
              className="w-full rounded-lg border border-border bg-input px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-muted-foreground">
              <Clock className="mr-1 inline h-3 w-3" />
              Sequence Name
            </label>
            <input
              type="text"
              value={currentSequenceName}
              onChange={(e) => setSequenceName(e.target.value)}
              placeholder="e.g., gentle_sway_01"
              disabled={isRecording}
              className="w-full rounded-lg border border-border bg-input px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
            />
          </div>
        </div>

        {/* Recording Controls */}
        <div className="flex items-center gap-2">
          {!isRecording ? (
            <button
              onClick={handleStartRecording}
              className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-red-500 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-red-600"
            >
              <Circle className="h-4 w-4 fill-current" />
              Start Recording
            </button>
          ) : (
            <button
              onClick={handleStopRecording}
              className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-secondary px-4 py-2.5 text-sm font-medium text-secondary-foreground transition-colors hover:bg-secondary/80"
            >
              <Square className="h-4 w-4" />
              Stop Recording
            </button>
          )}

          <button
            onClick={() => setShowLoadDialog(true)}
            className="flex items-center justify-center rounded-lg bg-secondary px-3 py-2.5 text-muted-foreground transition-colors hover:bg-secondary/80 hover:text-foreground"
          >
            <FolderOpen className="h-4 w-4" />
          </button>
        </div>

        {/* Events Count */}
        {recordedEvents.length > 0 && !isRecording && (
          <div className="rounded-lg bg-muted/50 p-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">
                Recorded Events: {recordedEvents.length}
              </span>
              <span className="text-muted-foreground">
                Duration:{" "}
                {formatTime(
                  recordedEvents[recordedEvents.length - 1]?.timestamp || 0
                )}
              </span>
            </div>
          </div>
        )}

        {/* Save & Play */}
        {recordedEvents.length > 0 && !isRecording && (
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={!currentSequenceLabel.trim() || !currentSequenceName.trim()}
              className={cn(
                "flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
                (!currentSequenceLabel.trim() || !currentSequenceName.trim()) &&
                  "cursor-not-allowed opacity-50"
              )}
            >
              <Save className="h-4 w-4" />
              Save Sequence
            </button>
          </div>
        )}

        {/* Loaded Sequence Playback */}
        {loadedSequence && (
          <div className="rounded-lg border border-primary/30 bg-primary/5 p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium text-primary">
                {loadedSequence.label} / {loadedSequence.name}
              </span>
              <span className="text-xs text-muted-foreground">
                {loadedSequence.events.length} events
              </span>
            </div>

            {isPlaying && (
              <div className="mb-2 h-1.5 w-full rounded-full bg-muted overflow-hidden">
                <motion.div
                  className="h-1.5 rounded-full bg-primary"
                  initial={{ width: 0 }}
                  animate={{ width: `${playbackProgress}%` }}
                />
              </div>
            )}

            <div className="flex gap-2">
              {!isPlaying ? (
                <button
                  onClick={handlePlay}
                  className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                >
                  <Play className="h-4 w-4" />
                  Play
                </button>
              ) : (
                <button
                  onClick={handleStop}
                  className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-secondary px-3 py-2 text-sm font-medium text-secondary-foreground transition-colors hover:bg-secondary/80"
                >
                  <Pause className="h-4 w-4" />
                  Stop
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Load Dialog */}
      <AnimatePresence>
        {showLoadDialog && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
              onClick={() => setShowLoadDialog(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-border bg-card p-6 shadow-xl"
            >
              <h3 className="mb-4 text-lg font-semibold text-foreground">
                Load Sequence
              </h3>

              {Object.keys(groupedSequences).length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No saved sequences found.
                </p>
              ) : (
                <div className="max-h-64 space-y-4 overflow-y-auto">
                  {Object.entries(groupedSequences).map(([label, names]) => (
                    <div key={label}>
                      <span className="mb-2 block text-xs font-medium text-muted-foreground">
                        {label}
                      </span>
                      <div className="space-y-1">
                        {names.map((name) => (
                          <button
                            key={name}
                            onClick={() => handleLoad(name)}
                            className="flex w-full items-center justify-between rounded-lg bg-muted px-3 py-2 text-sm text-foreground transition-colors hover:bg-muted/80"
                          >
                            {name}
                            <FolderOpen className="h-3.5 w-3.5 text-muted-foreground" />
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <button
                onClick={() => setShowLoadDialog(false)}
                className="mt-4 w-full rounded-lg bg-secondary px-4 py-2 text-sm font-medium text-secondary-foreground transition-colors hover:bg-secondary/80"
              >
                Cancel
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
