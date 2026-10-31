import { getDb } from "./connection";
import { modificationLogs } from "@db/schema";
import { eq, desc } from "drizzle-orm";

export async function findAllLogs(limit?: number) {
  return getDb().query.modificationLogs.findMany({
    orderBy: [desc(modificationLogs.createdAt)],
    limit,
    with: { agent: true },
  });
}

export async function findLogsByAgentId(agentId: number) {
  return getDb().query.modificationLogs.findMany({
    where: eq(modificationLogs.agentId, agentId),
    orderBy: [desc(modificationLogs.createdAt)],
    with: { agent: true },
  });
}

export async function createLog(data: {
  agentId: number;
  action: string;
  details: string;
  metadata?: Record<string, unknown>;
}) {
  const [{ id }] = await getDb()
    .insert(modificationLogs)
    .values({
      agentId: data.agentId,
      action: data.action as "spawn" | "build_capability" | "modify_architecture" | "self_refactor" | "discover_need" | "merge" | "deprecate",
      details: data.details,
      metadata: data.metadata || {},
    })
    .$returningId();

  return getDb().query.modificationLogs.findFirst({
    where: eq(modificationLogs.id, id),
    with: { agent: true },
  });
}
