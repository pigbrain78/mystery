import {
  mysqlTable,
  mysqlEnum,
  serial,
  varchar,
  text,
  timestamp,
  bigint,
  int,
  json,
} from "drizzle-orm/mysql-core";

export const users = mysqlTable("users", {
  id: serial("id").primaryKey(),
  unionId: varchar("unionId", { length: 255 }).notNull().unique(),
  name: varchar("name", { length: 255 }),
  email: varchar("email", { length: 320 }),
  avatar: text("avatar"),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt")
    .defaultNow()
    .notNull()
    .$onUpdate(() => new Date()),
  lastSignInAt: timestamp("lastSignInAt").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

// ─── Genesis Engine Schema ───

export const agents = mysqlTable("agents", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 255 }).notNull(),
  purpose: text("purpose").notNull(),
  status: mysqlEnum("status", [
    "spawning",
    "observing",
    "analyzing",
    "building",
    "running",
    "completed",
    "error",
    "idle",
  ])
    .default("idle")
    .notNull(),
  agentType: mysqlEnum("agentType", ["root", "worker", "manager", "meta"])
    .default("worker")
    .notNull(),
  parentId: bigint("parentId", { mode: "number", unsigned: true }),
  depth: int("depth").default(0).notNull(),
  code: text("code"),
  insight: text("insight"),
  spawnedCount: int("spawnedCount").default(0).notNull(),
  avatar: varchar("avatar", { length: 50 }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt")
    .defaultNow()
    .notNull()
    .$onUpdate(() => new Date()),
});

export type Agent = typeof agents.$inferSelect;
export type InsertAgent = typeof agents.$inferInsert;

export const capabilities = mysqlTable("capabilities", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 255 }).notNull(),
  description: text("description").notNull(),
  builderAgentId: bigint("builderAgentId", {
    mode: "number",
    unsigned: true,
  }).notNull(),
  dependsOnCapabilityId: bigint("dependsOnCapabilityId", {
    mode: "number",
    unsigned: true,
  }),
  code: text("code"),
  language: varchar("language", { length: 50 }).default("typescript"),
  status: mysqlEnum("status", ["designing", "building", "testing", "ready", "deprecated"])
    .default("designing")
    .notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type Capability = typeof capabilities.$inferSelect;
export type InsertCapability = typeof capabilities.$inferInsert;

export const tasks = mysqlTable("tasks", {
  id: serial("id").primaryKey(),
  agentId: bigint("agentId", { mode: "number", unsigned: true }).notNull(),
  description: text("description").notNull(),
  status: mysqlEnum("status", ["pending", "in_progress", "completed", "failed"])
    .default("pending")
    .notNull(),
  result: text("result"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  completedAt: timestamp("completedAt"),
});

export type Task = typeof tasks.$inferSelect;
export type InsertTask = typeof tasks.$inferInsert;

export const modificationLogs = mysqlTable("modificationLogs", {
  id: serial("id").primaryKey(),
  agentId: bigint("agentId", { mode: "number", unsigned: true }).notNull(),
  action: mysqlEnum("action", [
    "spawn",
    "build_capability",
    "modify_architecture",
    "self_refactor",
    "discover_need",
    "merge",
    "deprecate",
  ]).notNull(),
  details: text("details").notNull(),
  metadata: json("metadata"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type ModificationLog = typeof modificationLogs.$inferSelect;
export type InsertModificationLog = typeof modificationLogs.$inferInsert;

export const agentRelationships = mysqlTable("agentRelationships", {
  id: serial("id").primaryKey(),
  sourceAgentId: bigint("sourceAgentId", { mode: "number", unsigned: true }).notNull(),
  targetAgentId: bigint("targetAgentId", { mode: "number", unsigned: true }).notNull(),
  relationshipType: mysqlEnum("relationshipType", [
    "spawns",
    "depends_on",
    "communicates_with",
    "replaces",
  ]).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type AgentRelationship = typeof agentRelationships.$inferSelect;
export type InsertAgentRelationship = typeof agentRelationships.$inferInsert;
