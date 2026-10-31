import { getDb } from "./connection";
import { agentRelationships } from "@db/schema";
import { eq } from "drizzle-orm";

export async function findAllRelationships() {
  return getDb().query.agentRelationships.findMany({
    with: { source: true, target: true },
  });
}

export async function findRelationshipsBySourceId(sourceAgentId: number) {
  return getDb().query.agentRelationships.findMany({
    where: eq(agentRelationships.sourceAgentId, sourceAgentId),
    with: { target: true },
  });
}

export async function createRelationship(data: {
  sourceAgentId: number;
  targetAgentId: number;
  relationshipType: string;
}) {
  const [{ id }] = await getDb()
    .insert(agentRelationships)
    .values({
      sourceAgentId: data.sourceAgentId,
      targetAgentId: data.targetAgentId,
      relationshipType: data.relationshipType as "spawns" | "depends_on" | "communicates_with" | "replaces",
    })
    .$returningId();

  return getDb().query.agentRelationships.findFirst({
    where: eq(agentRelationships.id, id),
    with: { source: true, target: true },
  });
}
