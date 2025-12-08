"use client";

import { signOut } from "next-auth/react";
import { Button } from "@heroui/react";

export function LogoutButton() {
  return (
    <Button
      onPress={() => signOut({ callbackUrl: '/login' })}
      variant="bordered"
      size="sm"
      className="ml-3 bg-white text-gray-700"
      title="Cerrar sesión"
    >
      Salir
    </Button>
  );
}

export default LogoutButton;
