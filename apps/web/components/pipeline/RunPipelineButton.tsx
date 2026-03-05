"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/Button";
import { triggerPipeline } from "@/lib/api";

interface RunPipelineButtonProps {
  onComplete?: () => void;
}

export default function RunPipelineButton({ onComplete }: RunPipelineButtonProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRun() {
    setLoading(true);
    setError(null);
    try {
      await triggerPipeline();
      onComplete?.();
      router.refresh();
    } catch (err: any) {
      setError(err.message ?? "Pipeline failed");
      onComplete?.();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <Button onClick={handleRun} isLoading={loading} disabled={loading} size="lg">
        {loading ? "Running Pipeline…" : "Run Pipeline"}
      </Button>
      {error && (
        <p className="mt-2 text-sm text-red-400">{error}</p>
      )}
    </div>
  );
}
