import { heroui } from "@heroui/react";

/** @type {import('tailwindcss').Config} */
const heroConfig = {
  content: [
    "./node_modules/@heroui/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  plugins: [heroui()],
};

export default heroConfig;
