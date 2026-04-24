"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/analytics", label: "Analytics" },
];

export function PlatformNav() {
  const pathname = usePathname();

  return (
    <nav className="flex items-center gap-2 rounded-full border border-white/8 bg-white/4 p-1">
      {NAV_ITEMS.map((item) => {
        const isActive = pathname === item.href;

        return (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded-full px-4 py-2 text-sm font-medium transition ${
              isActive
                ? "bg-[var(--broker-accent)] text-[var(--broker-bg)]"
                : "text-[var(--broker-text-muted)] hover:bg-white/6 hover:text-[var(--broker-text)]"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
