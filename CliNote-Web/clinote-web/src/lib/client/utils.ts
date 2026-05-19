import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function calculateAge(dateOfBirth: string | Date): number {
  const today = new Date();
  const birth = new Date(dateOfBirth);
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  return age;
}

export function getRiskColor(risk: "LOW" | "MEDIUM" | "HIGH"): string {
  switch (risk) {
    case "LOW":
      return "text-green-600";
    case "MEDIUM":
      return "text-amber-500";
    case "HIGH":
      return "text-red-600";
  }
}

export function getRiskBgColor(risk: "LOW" | "MEDIUM" | "HIGH"): string {
  switch (risk) {
    case "LOW":
      return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
    case "MEDIUM":
      return "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200";
    case "HIGH":
      return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
  }
}

export function getAlertPriorityColor(priority: "CRITICAL" | "WARNING" | "INFO"): string {
  switch (priority) {
    case "CRITICAL":
      return "bg-red-50 border-red-200 text-red-800 dark:bg-red-950 dark:border-red-800 dark:text-red-200";
    case "WARNING":
      return "bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-950 dark:border-amber-800 dark:text-amber-200";
    case "INFO":
      return "bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-950 dark:border-blue-800 dark:text-blue-200";
  }
}
