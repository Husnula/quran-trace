import TraceApp from "@/components/TraceApp";

// Static export: no dynamic rendering
export const dynamic = "force-static";

export default function Home() {
  return <TraceApp />;
}
