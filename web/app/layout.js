import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata = {
  title: "Ai-doc",
  description: "Court document field extraction with local LLMs",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-zinc-950 text-zinc-100 antialiased">
        <NavBar />
        <main className="mx-auto max-w-6xl px-4 pb-16">{children}</main>
      </body>
    </html>
  );
}
