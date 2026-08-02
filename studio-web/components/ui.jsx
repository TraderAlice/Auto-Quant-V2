import Link from "next/link";

const toneByState = {
  known: "known",
  partial: "partial",
  delayed: "delayed",
  revised: "revised",
  restricted: "restricted",
  missing: "missing",
  健康: "known",
  成功: "known",
  运行中: "delayed",
  排队: "partial",
  失败: "missing",
  受限: "restricted",
  部分: "partial",
  通过: "known",
  注意: "delayed",
  invalid: "missing",
  unavailable: "missing",
};

export function StatusChip({ state, children = state }) {
  return <span className={`status-chip ${toneByState[state] || "partial"}`}>{children}</span>;
}

export function PageHeading({ eyebrow, title, description, actions }) {
  return (
    <header className="page-heading">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {description ? <p className="page-description">{description}</p> : null}
      </div>
      {actions ? <div className="page-actions">{actions}</div> : null}
    </header>
  );
}

export function Panel({ title, meta, action, children, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      {(title || action) ? (
        <header className="panel-header">
          <div>
            {title ? <h2>{title}</h2> : null}
            {meta ? <p>{meta}</p> : null}
          </div>
          {action}
        </header>
      ) : null}
      <div className="panel-body">{children}</div>
    </section>
  );
}

export function Metric({ label, value, detail, tone = "" }) {
  return (
    <div className={`metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}

export function ObjectLink({ href, label, id }) {
  return (
    <Link className="object-link" href={href}>
      <span>{label}</span>
      <b className="mono">{id}</b>
    </Link>
  );
}
