import { authRouter } from "./auth-router";
import { createRouter, publicQuery } from "./middleware";
import { agentRouter } from "./agentRouter";
import { capabilityRouter } from "./capabilityRouter";
import { taskRouter } from "./taskRouter";
import { modificationLogRouter } from "./modificationLogRouter";
import { genesisRouter } from "./genesisRouter";

export const appRouter = createRouter({
  ping: publicQuery.query(() => ({ ok: true, ts: Date.now() })),
  auth: authRouter,
  agent: agentRouter,
  capability: capabilityRouter,
  task: taskRouter,
  log: modificationLogRouter,
  genesis: genesisRouter,
});

export type AppRouter = typeof appRouter;
