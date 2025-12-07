"use client";

import { signOut } from "next-auth/react";

export function LogoutButton() {
  return (
    <button
      onClick={() => signOut({ callbackUrl: '/login' })}
      className="ml-3 inline-flex items-center gap-2 px-3 py-1.5 border rounded-md bg-white text-sm text-gray-700 hover:bg-gray-50"
      title="Cerrar sesión"
    >
      Salir
    </button>
  );
}

export default LogoutButton;
