import { z } from "zod";
import { createRouter, publicQuery } from "./middleware";
import {
  findAllTasks,
  findTasksByAgentId,
  createTask,
  updateTaskStatus,
} from "./queries/tasks";

export const taskRouter = createRouter({
  list: publicQuery.query(() => findAllTasks()),

  byAgent: publicQuery
    .input(z.object({ agentId: z.number() }))
    .query(({ input }) => findTasksByAgentId(input.agentId)),

  create: publicQuery
    .input(
      z.object({
        agentId: z.number(),
        description: z.string().min(1),
        status: z.enum(["pending", "in_progress", "completed", "failed"]).optional(),
      })
    )
    .mutation(({ input }) => createTask(input)),

  updateStatus: publicQuery
    .input(
      z.object({
        id: z.number(),
        status: z.enum(["pending", "in_progress", "completed", "failed"]),
        result: z.string().optional(),
      })
    )
    .mutation(({ input }) => updateTaskStatus(input.id, input.status, input.result)),
});
