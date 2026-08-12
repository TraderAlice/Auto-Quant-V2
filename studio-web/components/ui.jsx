"use client";

import Link from "next/link";
import { Badge, Box, Button as MantineButton, Group, Paper, Stack, Table, Text, Title } from "@mantine/core";

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
  success: "known",
  succeeded: "known",
  completed: "known",
  valid: "known",
  available: "known",
  running: "delayed",
  queued: "partial",
  failed: "missing",
  error: "missing",
};

export function StatusChip({ state, children = state }) {
  const tone = toneByState[state] || "partial";
  return <Badge className={`status-chip ${tone}`} data-tone={tone} variant="outline" radius="xs">{children}</Badge>;
}

export function PageHeading({ eyebrow, title, description, actions }) {
  return (
    <Group component="header" className="page-heading" justify="space-between" align="flex-start" wrap="wrap">
      <Box>
        {eyebrow ? <Text component="p" className="eyebrow">{eyebrow}</Text> : null}
        <Title order={1}>{title}</Title>
        {description ? <Text component="p" className="page-description">{description}</Text> : null}
      </Box>
      {actions ? <Group className="page-actions" gap="xs">{actions}</Group> : null}
    </Group>
  );
}

export function Panel({ title, meta, action, children, className = "" }) {
  return (
    <Paper component="section" className={`panel ${className}`} radius="xs" withBorder>
      {(title || action) ? (
        <Group component="header" className="panel-header" justify="space-between" align="flex-start" wrap="nowrap">
          <Box>
            {title ? <Title order={2}>{title}</Title> : null}
            {meta ? <Text component="p">{meta}</Text> : null}
          </Box>
          {action}
        </Group>
      ) : null}
      <Box className="panel-body">{children}</Box>
    </Paper>
  );
}

export function Metric({ label, value, detail, tone = "" }) {
  return (
    <Stack className={`metric ${tone}`} gap={2}>
      <Text component="span">{label}</Text>
      <Text component="strong">{value}</Text>
      {detail ? <Text component="small">{detail}</Text> : null}
    </Stack>
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

const buttonVariant = {
  primary: "filled",
  secondary: "default",
  quiet: "subtle",
};

export function Button({ variant = "primary", className = "", ...props }) {
  return (
    <MantineButton
      className={`aq-button aq-button-${variant} ${className}`}
      variant={buttonVariant[variant] || variant}
      radius="xs"
      size="xs"
      {...props}
    />
  );
}

export function ButtonLink({ href, variant = "secondary", className = "", ...props }) {
  return (
    <MantineButton
      component={Link}
      href={href}
      className={`aq-button aq-button-${variant} ${className}`}
      variant={buttonVariant[variant] || variant}
      radius="xs"
      size="xs"
      {...props}
    />
  );
}

export function EmptyState({ title, detail, children, className = "" }) {
  return (
    <Stack className={`empty-state ${className}`} gap={4} role="status">
      <Text component="strong">{title}</Text>
      {detail ? <Text component="span">{detail}</Text> : null}
      {children}
    </Stack>
  );
}

export function FormField({ label, htmlFor, help, error, children, className = "" }) {
  return (
    <Stack className={`form-field ${className}`} gap={4}>
      {label ? <Text component="label" htmlFor={htmlFor}>{label}</Text> : null}
      {children}
      {help ? <Text component="small" className="muted">{help}</Text> : null}
      {error ? <Text component="small" c="red.4">{error}</Text> : null}
    </Stack>
  );
}

export function DataTable({ children, minWidth = 620, className = "" }) {
  return (
    <Table.ScrollContainer className={`table-wrap ${className}`} minWidth={minWidth}>
      <Table striped highlightOnHover withTableBorder={false} verticalSpacing="xs" horizontalSpacing="sm">
        {children}
      </Table>
    </Table.ScrollContainer>
  );
}
