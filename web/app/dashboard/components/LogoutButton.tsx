"use client";

import { signOut } from "next-auth/react";
import { Button } from "@heroui/react";
import { LogOut } from "lucide-react";

export function LogoutButton() {
  return (
    <Button
      onPress={() => signOut({ callbackUrl: '/login' })}
      size="md"
      className="bg-gradient-to-r from-red-500 to-red-600 text-white font-semibold shadow-lg hover:shadow-xl hover:from-red-600 hover:to-red-700 transition-all transform hover:scale-105 duration-200"
      startContent={<LogOut size={20} />}
      title="Cerrar sesión"
    >
      Salir
    </Button>
  );
}

export default LogoutButton;
