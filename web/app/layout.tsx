import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Trace Qur'an - Lembar Latihan Menulis Arab",
  description:
    "Ubah PDF Al-Qur'an menjadi lembar latihan menulis Arab. Teks Arab samar, border ornamen tetap hitam. 100% di browser, tanpa upload ke server.",
  openGraph: {
    title: "Trace Qur'an",
    description: "Buat lembar trace Al-Qur'an langsung di browser",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-[var(--color-bg-base)] font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
