"use client";

import { usePathname } from "next/navigation";
import { useTheme } from "@/components/providers/ThemeProvider";
import { Menu, Sun, Moon } from "lucide-react";
import { clsx } from "clsx";

interface HeaderProps {
  userName: string;
  onMenuClick: () => void;
}

function getPageTitle(pathname: string): string {
  if (pathname === "/dashboard") return "Dashboard";
  if (pathname === "/patients/new") return "Add Patient";
  if (pathname.match(/^\/patients\/[^/]+\/report$/)) return "Patient Report";
  if (pathname.match(/^\/patients\/[^/]+$/)) return "Patient Detail";
  if (pathname === "/patients") return "Patients";
  if (pathname === "/alerts") return "Alerts";
  if (pathname === "/model-performance") return "Model Performance";
  return "ClinNote";
}

export function Header({ userName, onMenuClick }: HeaderProps) {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const pageTitle = getPageTitle(pathname);

  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center border-b border-slate-200 bg-white px-4 dark:border-slate-700 dark:bg-slate-800 lg:px-6">
      {/* Mobile menu button */}
      <button
        onClick={onMenuClick}
        className="mr-3 rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700 lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Page title */}
      <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
        {pageTitle}
      </h1>

      {/* Right side */}
      <div className="ml-auto flex items-center gap-3">
        {/* Dark mode toggle */}
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-200"
          title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
        >
          {theme === "light" ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
        </button>

        {/* User avatar */}
        <div
          className={clsx(
            "flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white"
          )}
        >
          {userName
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2)}
        </div>
      </div>
    </header>
  );
}
