import Link from "next/link";
import { EventWorkbench } from "@/components/event-workbench";
import { PageHeading } from "@/components/ui";

export default function EventsPage() {
  return (
    <>
      <PageHeading
        eyebrow="Event cohorts"
        title="事件工作台"
        description="圈选事件、保存两组成员规则，在同一口径下比较，并把差异证据转成候选因子。"
        actions={<Link className="button-secondary" href="/replay">返回回放圈选</Link>}
      />
      <EventWorkbench />
    </>
  );
}
