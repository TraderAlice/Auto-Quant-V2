import { EventWorkbench } from "@/components/event-workbench";
import { ButtonLink, PageHeading } from "@/components/ui";

export default function EventsPage() {
  return (
    <>
      <PageHeading
        eyebrow="Event cohorts"
        title="事件工作台"
        description="圈选事件、保存两组成员规则，在同一口径下比较，并把差异证据转成候选因子。"
        actions={<ButtonLink href="/replay">返回回放圈选</ButtonLink>}
      />
      <EventWorkbench />
    </>
  );
}
