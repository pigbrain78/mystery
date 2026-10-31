import { getDb } from "./connection";
import { tasks } from "@db/schema";
import { eq, desc } from "drizzle-orm";

export async function findAllTasks() {
  return getDb().query.tasks.findMany({
    orderBy: [desc(tasks.createdAt)],
    with: { agent: true },
  });
}

export async function findTasksByAgentId(agentId: number) {
  return getDb().query.tasks.findMany({
    where: eq(tasks.agentId, agentId),
    orderBy: [desc(tasks.createdAt)],
  });
}

export async function createTask(data: {
  agentId: number;
  description: string;
  status?: string;
}) {
  const [{ id }] = await getDb()
    .insert(tasks)
    .values({
      agentId: data.agentId,
      description: data.description,
      status: (data.status || "pending") as "pending" | "in_progress" | "completed" | "failed",
    })
    .$returningId();

  return getDb().query.tasks.findFirst({
    where: eq(tasks.id, id),
    with: { agent: true },
  });
}

export async function updateTaskStatus(id: number, status: string, result?: string) {
  const update: Record<string, unknown> = {
    status: status as "pending" | "in_progress" | "completed" | "failed",
  };
  if (result !== undefined) update.result = result;
  if (status === "completed" || status === "failed") {
    update.completedAt = new Date();
  }

  await getDb()
    .update(tasks)
    .set(update)
    .where(eq(tasks.id, id));

  return getDb().query.tasks.findFirst({
    where: eq(tasks.id, id),
    with: { agent: true },
  });
}
