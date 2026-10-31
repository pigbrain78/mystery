import { getDb } from "./connection";
import { capabilities } from "@db/schema";
import { eq, desc } from "drizzle-orm";

export async function findAllCapabilities() {
  return getDb().query.capabilities.findMany({
    orderBy: [desc(capabilities.createdAt)],
    with: { builder: true },
  });
}

export async function findCapabilityById(id: number) {
  return getDb().query.capabilities.findFirst({
    where: eq(capabilities.id, id),
    with: { builder: true },
  });
}

export async function findCapabilitiesByAgentId(agentId: number) {
  return getDb().query.capabilities.findMany({
    where: eq(capabilities.builderAgentId, agentId),
    orderBy: [desc(capabilities.createdAt)],
  });
}

export async function createCapability(data: {
  name: string;
  description: string;
  builderAgentId: number;
  dependsOnCapabilityId?: number;
  code?: string;
  language?: string;
  status?: string;
}) {
  const [{ id }] = await getDb()
    .insert(capabilities)
    .values({
      name: data.name,
      description: data.description,
      builderAgentId: data.builderAgentId,
      dependsOnCapabilityId: data.dependsOnCapabilityId,
      code: data.code,
      language: data.language || "typescript",
      status: (data.status || "designing") as "designing" | "building" | "testing" | "ready" | "deprecated",
    })
    .$returningId();

  return findCapabilityById(id);
}

export async function updateCapabilityStatus(id: number, status: string) {
  await getDb()
    .update(capabilities)
    .set({ status: status as "designing" | "building" | "testing" | "ready" | "deprecated" })
    .where(eq(capabilities.id, id));
  return findCapabilityById(id);
}
