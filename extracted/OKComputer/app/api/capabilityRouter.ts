import { z } from "zod";
import { createRouter, publicQuery } from "./middleware";
import {
  findAllCapabilities,
  findCapabilityById,
  findCapabilitiesByAgentId,
  createCapability,
  updateCapabilityStatus,
} from "./queries/capabilities";

export const capabilityRouter = createRouter({
  list: publicQuery.query(() => findAllCapabilities()),

  byId: publicQuery
    .input(z.object({ id: z.number() }))
    .query(({ input }) => findCapabilityById(input.id)),

  byAgent: publicQuery
    .input(z.object({ agentId: z.number() }))
    .query(({ input }) => findCapabilitiesByAgentId(input.agentId)),

  create: publicQuery
    .input(
      z.object({
        name: z.string().min(1),
        description: z.string().min(1),
        builderAgentId: z.number(),
        dependsOnCapabilityId: z.number().optional(),
        code: z.string().optional(),
        language: z.string().default("typescript"),
        status: z.enum(["designing", "building", "testing", "ready", "deprecated"]).optional(),
      })
    )
    .mutation(({ input }) => createCapability(input)),

  updateStatus: publicQuery
    .input(
      z.object({
        id: z.number(),
        status: z.enum(["designing", "building", "testing", "ready", "deprecated"]),
      })
    )
    .mutation(({ input }) => updateCapabilityStatus(input.id, input.status)),
});
