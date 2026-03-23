import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// API helpers
export async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.statusText}`);
  return res.json();
}

export async function postJSON<T, D = unknown>(
  url: string,
  data?: D
): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data || {}),
  });
  if (!res.ok) throw new Error(`Failed to post ${url}: ${res.statusText}`);
  return res.json();
}

// Parse comma-separated OSC args
export function parseOSCArgs(raw: string): (number | string)[] {
  if (!raw.trim()) return [];
  return raw.split(",").map((item) => {
    const v = item.trim();
    if (/^-?\d+$/.test(v)) return parseInt(v, 10);
    if (/^-?\d+\.\d+$/.test(v)) return parseFloat(v);
    return v;
  });
}

// Clamp value between min and max
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

// Map value from one range to another
export function mapRange(
  value: number,
  inMin: number,
  inMax: number,
  outMin: number,
  outMax: number
): number {
  return ((value - inMin) * (outMax - outMin)) / (inMax - inMin) + outMin;
}

// Format milliseconds to mm:ss.ms
export function formatTime(ms: number): string {
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  const millis = Math.floor((ms % 1000) / 10);
  return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}.${millis.toString().padStart(2, "0")}`;
}

// Debounce function
export function debounce<T extends (...args: Parameters<T>) => void>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

// Throttle function
export function throttle<T extends (...args: Parameters<T>) => void>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let lastFunc: NodeJS.Timeout | null = null;
  let lastRan: number | null = null;
  return (...args: Parameters<T>) => {
    if (!lastRan) {
      func(...args);
      lastRan = Date.now();
    } else {
      if (lastFunc) clearTimeout(lastFunc);
      lastFunc = setTimeout(() => {
        if (Date.now() - lastRan! >= limit) {
          func(...args);
          lastRan = Date.now();
        }
      }, limit - (Date.now() - lastRan));
    }
  };
}

// Node type display info
export const NODE_TYPE_INFO: Record<
  string,
  { label: string; icon: string; color: string }
> = {
  kait: { label: "Kait", icon: "Zap", color: "text-amber-400" },
  sue: { label: "Sue", icon: "Flower2", color: "text-emerald-400" },
  sylvie: { label: "Sylvie", icon: "Sparkles", color: "text-sky-400" },
  face_track: { label: "Face Track", icon: "ScanFace", color: "text-pink-400" },
  unknown: { label: "Unknown", icon: "HelpCircle", color: "text-muted-foreground" },
};

// Emotion state colors
export const EMOTION_COLORS: Record<string, { bg: string; text: string; glow: string }> = {
  BLOOM: { bg: "bg-amber-600", text: "text-amber-50", glow: "glow-warning" },
  ALERT: { bg: "bg-red-600", text: "text-red-50", glow: "glow-destructive" },
  SOOTHE: { bg: "bg-emerald-600", text: "text-emerald-50", glow: "glow-success" },
  REST: { bg: "bg-secondary", text: "text-secondary-foreground", glow: "" },
};
