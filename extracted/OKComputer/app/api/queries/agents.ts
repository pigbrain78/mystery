import { getDb } from "./connection";
import { agents, modificationLogs } from "@db/schema";
import { eq, desc, isNull } from "drizzle-orm";

export async function findAllAgents() {
  return getDb().query.agents.findMany({
    orderBy: [desc(agents.createdAt)],
  });
}

export async function findAgentById(id: number) {
  return getDb().query.agents.findFirst({
    where: eq(agents.id, id),
    with: {
      children: true,
      capabilities: true,
      tasks: true,
      logs: {
        orderBy: [desc(modificationLogs.createdAt)],
        limit: 20,
      },
    },
  });
}

export async function findAgentTree(rootId?: number) {
  const allAgents = await getDb().query.agents.findMany({
    orderBy: [agents.depth, agents.createdAt],
  });

  if (!rootId) {
    return allAgents.filter((a) => a.parentId === null);
  }

  return allAgents;
}

export async function findChildrenByParentId(parentId: number) {
  return getDb().query.agents.findMany({
    where: eq(agents.parentId, parentId),
    orderBy: [agents.createdAt],
  });
}

export async function findRootAgents() {
  return getDb().query.agents.findMany({
    where: isNull(agents.parentId),
    orderBy: [desc(agents.createdAt)],
  });
}

export async function createAgent(data: {
  name: string;
  purpose: string;
  agentType: string;
  parentId?: number;
  depth: number;
  status?: string;
  code?: string;
  insight?: string;
  avatar?: string;
}) {
  const [{ id }] = await getDb()
    .insert(agents)
    .values({
      name: data.name,
      purpose: data.purpose,
      agentType: data.agentType as "root" | "worker" | "manager" | "meta",
      parentId: data.parentId,
      depth: data.depth,
      status: (data.status || "idle") as "spawning" | "observing" | "analyzing" | "building" | "running" | "completed" | "error" | "idle",
      code: data.code,
      insight: data.insight,
      avatar: data.avatar,
    })
    .$returningId();

  return findAgentById(id);
}

export async function updateAgentStatus(id: number, status: string) {
  await getDb()
    .update(agents)
    .set({ status: status as "spawning" | "observing" | "analyzing" | "building" | "running" | "completed" | "error" | "idle" })
    .where(eq(agents.id, id));
  return findAgentById(id);
}

export async function updateAgentCode(id: number, code: string) {
  await getDb()
    .update(agents)
    .set({ code })
    .where(eq(agents.id, id));
  return findAgentById(id);
}

export async function updateAgentInsight(id: number, insight: string) {
  await getDb()
    .update(agents)
    .set({ insight })
    .where(eq(agents.id, id));
  return findAgentById(id);
}

export async function incrementSpawnedCount(id: number) {
  const agent = await findAgentById(id);
  if (!agent) return null;
  await getDb()
    .update(agents)
    .set({ spawnedCount: agent.spawnedCount + 1 })
    .where(eq(agents.id, id));
  return findAgentById(id);
}

export async function deleteAgent(id: number) {
  await getDb().delete(agents).where(eq(agents.id, id));
}

export async function getAgentStats() {
  const allAgents = await findAllAgents();
  const totalAgents = allAgents.length;
  const activeAgents = allAgents.filter(
    (a) => a.status === "running" || a.status === "building" || a.status === "observing" || a.status === "analyzing"
  ).length;
  const maxDepth = allAgents.reduce((max, a) => Math.max(max, a.depth), 0);
  const metaAgents = allAgents.filter((a) => a.agentType === "meta").length;
  const managerAgents = allAgents.filter((a) => a.agentType === "manager").length;

  return { totalAgents, activeAgents, maxDepth, metaAgents, managerAgents };
}

export async function getRecentAgents(limit: number = 10) {
  return getDb().query.agents.findMany({
    orderBy: [desc(agents.createdAt)],
    limit,
  });
}
