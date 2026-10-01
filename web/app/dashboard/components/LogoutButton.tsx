"use client";

import { signOut } from "next-auth/react";
import { Button } from "@heroui/react";
import { LogOut } from "lucide-react";

export function LogoutButton() {
  return (
    <Button
      type="button"
      onPress={() => signOut({ callbackUrl: '/login' })}
      isIconOnly
      size="sm"
      variant="light"
      aria-label="Cerrar sesión"
      className="h-10 w-10 min-w-10 rounded-xl border border-white/10 text-[var(--foreground)]/60 transition-colors hover:border-rose-500/30 hover:bg-rose-500/10 hover:text-rose-400"
      title="Cerrar sesión"
    >
      <LogOut size={16} />
    </Button>
  );
}

export default LogoutButton;
