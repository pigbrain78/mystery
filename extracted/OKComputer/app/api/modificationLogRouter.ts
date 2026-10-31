import { z } from "zod";
import { createRouter, publicQuery } from "./middleware";
import {
  findAllLogs,
  findLogsByAgentId,
  createLog,
} from "./queries/modificationLogs";

export const modificationLogRouter = createRouter({
  list: publicQuery
    .input(z.object({ limit: z.number().optional() }).optional())
    .query(({ input }) => findAllLogs(input?.limit)),

  byAgent: publicQuery
    .input(z.object({ agentId: z.number() }))
    .query(({ input }) => findLogsByAgentId(input.agentId)),

  create: publicQuery
    .input(
      z.object({
        agentId: z.number(),
        action: z.enum([
          "spawn",
          "build_capability",
          "modify_architecture",
          "self_refactor",
          "discover_need",
          "merge",
          "deprecate",
        ]),
        details: z.string().min(1),
        metadata: z.record(z.string(), z.unknown()).optional(),
      })
    )
    .mutation(({ input }) => createLog(input)),
});
