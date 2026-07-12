import { Navbar } from "@/components/layout/Navbar";
import { Hero } from "@/components/hero/Hero";
import { AppDashboard } from "@/components/dashboard/AppDashboard";
import { About } from "@/components/about/About";

export default function Home() {
  return (
    <main className="min-h-screen">
      <Navbar />
      <Hero />
      <AppDashboard />
      <About />
    </main>
  );
}
