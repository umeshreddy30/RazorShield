import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'RazorShield — Autonomous Multi-Agent Risk Intelligence',
  description: 'Production-grade Multi-Agent Fraud Prevention & Real-Time Investigation Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#070A12] text-slate-100 antialiased selection:bg-blue-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}
