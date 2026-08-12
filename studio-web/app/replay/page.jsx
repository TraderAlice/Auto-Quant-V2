import { PageHeading } from "@/components/ui";
import { ReplayWorkbench } from "@/components/replay-workbench";

export default function ReplayPage() {
  return (
    <>
      <PageHeading
        eyebrow="Temporal replay"
        title="时序回放"
        description="回到历史时点 T，只检查当时真实可用的事件、行情、市场快照和因子信号。"
      />
      <ReplayWorkbench />
    </>
  );
}
