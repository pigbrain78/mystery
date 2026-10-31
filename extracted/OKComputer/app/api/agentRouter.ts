import { z } from "zod";
import { createRouter, publicQuery } from "./middleware";
import {
  findAllAgents,
  findAgentById,
  findAgentTree,
  findChildrenByParentId,
  findRootAgents,
  createAgent,
  updateAgentStatus,
  updateAgentCode,
  updateAgentInsight,
  incrementSpawnedCount,
  deleteAgent,
  getAgentStats,
  getRecentAgents,
} from "./queries/agents";

export const agentRouter = createRouter({
  list: publicQuery.query(() => findAllAgents()),

  byId: publicQuery
    .input(z.object({ id: z.number() }))
    .query(({ input }) => findAgentById(input.id)),

  tree: publicQuery
    .input(z.object({ rootId: z.number().optional() }).optional())
    .query(({ input }) => findAgentTree(input?.rootId)),

  children: publicQuery
    .input(z.object({ parentId: z.number() }))
    .query(({ input }) => findChildrenByParentId(input.parentId)),

  roots: publicQuery.query(() => findRootAgents()),

  create: publicQuery
    .input(
      z.object({
        name: z.string().min(1),
        purpose: z.string().min(1),
        agentType: z.enum(["root", "worker", "manager", "meta"]).default("worker"),
        parentId: z.number().optional(),
        depth: z.number().default(0),
        status: z.enum(["spawning", "observing", "analyzing", "building", "running", "completed", "error", "idle"]).optional(),
        code: z.string().optional(),
        insight: z.string().optional(),
        avatar: z.string().optional(),
      })
    )
    .mutation(({ input }) => createAgent(input)),

  updateStatus: publicQuery
    .input(
      z.object({
        id: z.number(),
        status: z.enum(["spawning", "observing", "analyzing", "building", "running", "completed", "error", "idle"]),
      })
    )
    .mutation(({ input }) => updateAgentStatus(input.id, input.status)),

  updateCode: publicQuery
    .input(z.object({ id: z.number(), code: z.string() }))
    .mutation(({ input }) => updateAgentCode(input.id, input.code)),

  updateInsight: publicQuery
    .input(z.object({ id: z.number(), insight: z.string() }))
    .mutation(({ input }) => updateAgentInsight(input.id, input.insight)),

  incrementSpawned: publicQuery
    .input(z.object({ id: z.number() }))
    .mutation(({ input }) => incrementSpawnedCount(input.id)),

  delete: publicQuery
    .input(z.object({ id: z.number() }))
    .mutation(({ input }) => deleteAgent(input.id)),

  stats: publicQuery.query(() => getAgentStats()),

  recent: publicQuery
    .input(z.object({ limit: z.number().default(10) }).optional())
    .query(({ input }) => getRecentAgents(input?.limit || 10)),
});
