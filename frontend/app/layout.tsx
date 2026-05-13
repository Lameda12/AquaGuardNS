import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "AquaGuard NS", description: "Marine Heatwave Early Warning System" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
