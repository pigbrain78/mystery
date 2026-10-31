import { relations } from "drizzle-orm";
import { agents, capabilities, tasks, modificationLogs, agentRelationships } from "./schema";

export const agentsRelations = relations(agents, ({ one, many }) => ({
  parent: one(agents, { fields: [agents.parentId], references: [agents.id] }),
  children: many(agents),
  capabilities: many(capabilities),
  tasks: many(tasks),
  logs: many(modificationLogs),
  outgoingRelations: many(agentRelationships, { relationName: "source" }),
  incomingRelations: many(agentRelationships, { relationName: "target" }),
}));

export const capabilitiesRelations = relations(capabilities, ({ one }) => ({
  builder: one(agents, { fields: [capabilities.builderAgentId], references: [agents.id] }),
  dependsOn: one(capabilities, {
    fields: [capabilities.dependsOnCapabilityId],
    references: [capabilities.id],
  }),
}));

export const tasksRelations = relations(tasks, ({ one }) => ({
  agent: one(agents, { fields: [tasks.agentId], references: [agents.id] }),
}));

export const modificationLogsRelations = relations(modificationLogs, ({ one }) => ({
  agent: one(agents, { fields: [modificationLogs.agentId], references: [agents.id] }),
}));

export const agentRelationshipsRelations = relations(agentRelationships, ({ one }) => ({
  source: one(agents, { fields: [agentRelationships.sourceAgentId], references: [agents.id], relationName: "source" }),
  target: one(agents, { fields: [agentRelationships.targetAgentId], references: [agents.id], relationName: "target" }),
}));
