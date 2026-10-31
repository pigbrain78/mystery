import { z } from "zod";
import { createRouter, publicQuery } from "./middleware";
import { createAgent, updateAgentStatus, updateAgentInsight, incrementSpawnedCount } from "./queries/agents";
import { createCapability, updateCapabilityStatus } from "./queries/capabilities";
import { createTask } from "./queries/tasks";
import { createLog } from "./queries/modificationLogs";
import { createRelationship } from "./queries/agentRelationships";
import { getDb } from "./queries/connection";
import { agents, capabilities, tasks, modificationLogs, agentRelationships } from "@db/schema";

// ─── Simulation Data ───

const AVATARS = [
  "brain",
  "cpu",
  "network",
  "database",
  "shield",
  "eye",
  "code",
  "box",
  "git-branch",
  "terminal",
  "activity",
  "zap",
  "layers",
  "hexagon",
  "server",
  "cloud",
  "lock",
  "scan",
  "bot",
  "cog",
];

const INSIGHT_TEMPLATES: Record<string, string[]> = {
  root: [
    "Analyzing task decomposition vectors... I need specialized sub-agents for this.",
    "Initial topology analysis complete. The solution space requires {count} distinct capabilities.",
    "Self-assessment: I lack the specialized tooling for this domain. Spawning dedicated workers.",
    "The problem has a recursive structure. I will build a manager layer to coordinate.",
  ],
  observing: [
    "Monitoring environment signals for capability gaps...",
    "Scanning existing tool inventory against task requirements...",
    "Detected {count} missing primitives in current capability stack.",
    "Cross-referencing task needs with available APIs and data sources...",
  ],
  analyzing: [
    "Decomposing the problem into atomic operations...",
    "Building dependency graph for required capabilities...",
    "Found recursive sub-problem: {subproblem} requires its own tooling layer.",
    "Analyzing failure modes and building redundancy patterns...",
  ],
  building: [
    "Generating implementation for {capability}...",
    "Writing type-safe interfaces and validation schemas...",
    "Compiling capability module with error handling...",
    "Integrating new capability into agent runtime...",
  ],
  discover_need: [
    "Wait... to build {capability}, I first need {prerequisite}.",
    "Dependency chain analysis reveals: {capability} -> {prerequisite} -> ???",
    "Realization: This capability requires a lower-level primitive I don't have.",
    "The abstraction has a leak. I need to go one level deeper.",
  ],
  meta: [
    "I've been observing my own architecture. It can be improved.",
    "The current topology has {count} inefficiencies. Initiating self-refactor.",
    "Spawning a meta-agent to optimize the orchestration layer itself.",
    "The manager pattern is creating bottlenecks. Switching to mesh topology.",
  ],
};

function randomItem<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomAvatar(): string {
  return randomItem(AVATARS);
}

function generateAgentName(type: string, _depth: number, index: number): string {
  const prefixes: Record<string, string[]> = {
    root: ["Genesis", "Origin", "Alpha", "Prime", "Core"],
    worker: ["Builder", "Scout", "Forge", "Craft", "Weave", "Synth", "Make", "Build"],
    manager: ["Orchestrator", "Coordinator", "Director", "Conductor", "Architect", "Strategist"],
    meta: ["Nexus", "Singularity", "Observer", "Reflex", "Meta", "Omega", "Recursive"],
  };
  const prefixList = prefixes[type] || prefixes.worker;
  const prefix = randomItem(prefixList);
  const suffix = _depth === 0 ? "-0" : `-${_depth}.${index}`;
  return `${prefix}${suffix}`;
}

function generatePurpose(task: string, type: string, _depth: number): string {
  void _depth;
  if (type === "root") {
    return `Coordinate the full solution stack for: "${task}". Analyze, delegate, and orchestrate.`;
  }
  if (type === "manager") {
    return `Manage the ${task.toLowerCase()} pipeline. Coordinate workers, resolve conflicts, optimize throughput.`;
  }
  if (type === "meta") {
    return `Observe and optimize the agent topology itself. Identify inefficiencies, propose architectural changes.`;
  }
  return `Build and maintain the ${task.toLowerCase()} capability. Handle edge cases, ensure reliability.`;
}

function generateCodeSnippet(capabilityName: string): string {
  return `// ${capabilityName} - Auto-generated capability module
import { AgentRuntime } from '@genesis/core';

export class ${capabilityName.replace(/\s+/g, "")}Capability {
  private runtime: AgentRuntime;
  private config: CapabilityConfig;

  constructor(runtime: AgentRuntime, config: CapabilityConfig) {
    this.runtime = runtime;
    this.config = config;
  }

  async execute(input: unknown): Promise<CapabilityResult> {
    // Phase 1: Validate input schema
    const validated = await this.validate(input);
    
    // Phase 2: Execute core logic with retry
    const result = await this.runtime.executeWithRetry(
      () => this.process(validated),
      { maxRetries: 3, backoff: 'exponential' }
    );
    
    // Phase 3: Emit telemetry
    this.runtime.telemetry.emit('capability.executed', {
      capability: '${capabilityName}',
      duration: result.duration,
      success: result.success,
    });
    
    return result;
  }

  private async validate(input: unknown) { /* ... */ }
  private async process(input: unknown) { /* ... */ }
}`;
}

// ─── Genesis Engine ───

interface SeedConfig {
  task: string;
  maxDepth: number;
  branchingFactor: number;
  enableMeta: boolean;
}

interface SimulationStep {
  action: string;
  agentId: number;
  details: string;
  metadata?: Record<string, unknown>;
}

async function simulateGenesis(config: SeedConfig): Promise<{ rootAgentId: number; steps: SimulationStep[] }> {
  const steps: SimulationStep[] = [];

  // Phase 1: Create root agent
  const rootAgent = await createAgent({
    name: generateAgentName("root", 0, 0),
    purpose: generatePurpose(config.task, "root", 0),
    agentType: "root",
    depth: 0,
    status: "observing",
    insight: randomItem(INSIGHT_TEMPLATES.root).replace("{count}", String(config.branchingFactor)),
    avatar: randomAvatar(),
  });

  if (!rootAgent) throw new Error("Failed to create root agent");

  steps.push({
    action: "spawn",
    agentId: rootAgent.id,
    details: `Root agent spawned for task: "${config.task}"`,
    metadata: { type: "root", depth: 0 },
  });

  await createLog({
    agentId: rootAgent.id,
    action: "spawn",
    details: `Root agent "${rootAgent.name}" initialized for task: "${config.task}"`,
    metadata: { task: config.task, depth: 0 },
  });

  // Phase 2: Root agent discovers needs and spawns children
  await updateAgentStatus(rootAgent.id, "analyzing");
  const needs = discoverNeeds(config.task, config.branchingFactor);

  for (let i = 0; i < needs.length; i++) {
    const need = needs[i];
    const workerName = generateAgentName("worker", 1, i);

    // Log the discovery
    await createLog({
      agentId: rootAgent.id,
      action: "discover_need",
      details: `Discovered need: ${need.name} - ${need.description}`,
      metadata: { needName: need.name, hasSubNeeds: need.subNeeds.length > 0 },
    });

    steps.push({
      action: "discover_need",
      agentId: rootAgent.id,
      details: `Need discovered: ${need.name}`,
      metadata: { needName: need.name },
    });

    // Spawn worker agent
    const workerAgent = await createAgent({
      name: workerName,
      purpose: generatePurpose(need.name, "worker", 1),
      agentType: "worker",
      parentId: rootAgent.id,
      depth: 1,
      status: "spawning",
      avatar: randomAvatar(),
    });

    if (!workerAgent) continue;

    await incrementSpawnedCount(rootAgent.id);
    await createRelationship({
      sourceAgentId: rootAgent.id,
      targetAgentId: workerAgent.id,
      relationshipType: "spawns",
    });

    await createLog({
      agentId: rootAgent.id,
      action: "spawn",
      details: `Spawned worker "${workerName}" to handle: ${need.name}`,
      metadata: { childId: workerAgent.id, childName: workerName },
    });

    steps.push({
      action: "spawn",
      agentId: rootAgent.id,
      details: `Spawned worker: ${workerName}`,
      metadata: { childId: workerAgent.id },
    });

    // Worker builds its capability
    await updateAgentStatus(workerAgent.id, "building");
    const capability = await createCapability({
      name: need.name,
      description: need.description,
      builderAgentId: workerAgent.id,
      code: generateCodeSnippet(need.name),
      status: "building",
    });

    await createTask({
      agentId: workerAgent.id,
      description: `Build ${need.name} capability`,
      status: "in_progress",
    });

    await createLog({
      agentId: workerAgent.id,
      action: "build_capability",
      details: `Building capability: ${need.name}`,
      metadata: { capabilityId: capability?.id },
    });

    steps.push({
      action: "build_capability",
      agentId: workerAgent.id,
      details: `Building: ${need.name}`,
    });

    // Check depth for sub-needs
    if (config.maxDepth > 1 && need.subNeeds.length > 0) {
      await updateAgentStatus(workerAgent.id, "observing");
      await updateAgentInsight(
        workerAgent.id,
        randomItem(INSIGHT_TEMPLATES.discover_need)
          .replace("{capability}", need.name)
          .replace("{prerequisite}", need.subNeeds[0].name)
      );

      // Create sub-agents for sub-needs
      for (let j = 0; j < need.subNeeds.length; j++) {
        const subNeed = need.subNeeds[j];
        const subName = generateAgentName("worker", 2, j);

        await createLog({
          agentId: workerAgent.id,
          action: "discover_need",
          details: `Sub-need discovered: ${subNeed.name} (prerequisite for ${need.name})`,
          metadata: { prerequisiteFor: need.name },
        });

        const subAgent = await createAgent({
          name: subName,
          purpose: generatePurpose(subNeed.name, "worker", 2),
          agentType: "worker",
          parentId: workerAgent.id,
          depth: 2,
          status: "building",
          avatar: randomAvatar(),
        });

        if (!subAgent) continue;

        await incrementSpawnedCount(workerAgent.id);
        await createRelationship({
          sourceAgentId: workerAgent.id,
          targetAgentId: subAgent.id,
          relationshipType: "depends_on",
        });

        const subCapability = await createCapability({
          name: subNeed.name,
          description: subNeed.description,
          builderAgentId: subAgent.id,
          dependsOnCapabilityId: capability?.id,
          code: generateCodeSnippet(subNeed.name),
          status: "building",
        });

        await createTask({
          agentId: subAgent.id,
          description: `Build ${subNeed.name} (prerequisite for ${need.name})`,
          status: "in_progress",
        });

        await createLog({
          agentId: subAgent.id,
          action: "build_capability",
          details: `Building sub-capability: ${subNeed.name}`,
          metadata: { capabilityId: subCapability?.id, parentCapability: capability?.id },
        });

        steps.push({
          action: "spawn",
          agentId: workerAgent.id,
          details: `Spawned sub-worker: ${subName}`,
          metadata: { childId: subAgent.id, depth: 2 },
        });

        // Mark sub-agent as completed after a simulated delay
        await updateAgentStatus(subAgent.id, "running");
        if (subCapability) {
          await updateCapabilityStatus(subCapability.id, "ready");
        }
      }
    }

    // Mark worker as running
    await updateAgentStatus(workerAgent.id, "running");
    if (capability) {
      await updateCapabilityStatus(capability.id, "ready");
    }
  }

  // Phase 3: Meta-layer (if enabled)
  if (config.enableMeta && config.maxDepth >= 2) {
    const metaAgent = await createAgent({
      name: generateAgentName("meta", 1, 0),
      purpose: generatePurpose("topology optimization", "meta", 1),
      agentType: "meta",
      parentId: rootAgent.id,
      depth: 1,
      status: "observing",
      insight: randomItem(INSIGHT_TEMPLATES.meta).replace("{count}", String(Math.floor(Math.random() * 5) + 1)),
      avatar: randomAvatar(),
    });

    if (metaAgent) {
      await incrementSpawnedCount(rootAgent.id);
      await createRelationship({
        sourceAgentId: rootAgent.id,
        targetAgentId: metaAgent.id,
        relationshipType: "spawns",
      });

      await createLog({
        agentId: rootAgent.id,
        action: "spawn",
        details: `Spawned meta-agent "${metaAgent.name}" for topology optimization`,
        metadata: { childId: metaAgent.id, type: "meta" },
      });

      await createLog({
        agentId: metaAgent.id,
        action: "modify_architecture",
        details: `Meta-agent analyzing current topology for optimization opportunities`,
      });

      steps.push({
        action: "spawn",
        agentId: rootAgent.id,
        details: `Spawned meta-agent: ${metaAgent.name}`,
        metadata: { childId: metaAgent.id, type: "meta" },
      });

      await updateAgentStatus(metaAgent.id, "running");
    }
  }

  // Mark root as running
  await updateAgentStatus(rootAgent.id, "running");

  return { rootAgentId: rootAgent.id, steps };
}

interface Need {
  name: string;
  description: string;
  subNeeds: Need[];
}

function discoverNeeds(task: string, count: number): Need[] {
  const taskLower = task.toLowerCase();

  const needPools: Record<string, Need[]> = {
    expense: [
      { name: "Transaction Parser", description: "Parse and normalize raw transaction data from multiple sources", subNeeds: [{ name: "OCR Engine", description: "Extract text from receipt images and PDFs", subNeeds: [] }, { name: "CSV Normalizer", description: "Standardize CSV formats from different banks", subNeeds: [] }] },
      { name: "Category Classifier", description: "ML-based categorization of expenses into tax categories", subNeeds: [{ name: "Embedding Model", description: "Generate semantic embeddings for transaction descriptions", subNeeds: [] }] },
      { name: "Budget Tracker", description: "Real-time budget monitoring with variance alerts", subNeeds: [{ name: "Time Series DB", description: "Efficient storage and querying of time-series budget data", subNeeds: [] }, { name: "Alert Engine", description: "Threshold-based notification system for budget overruns", subNeeds: [] }] },
      { name: "Report Generator", description: "Automated monthly and quarterly financial reports", subNeeds: [{ name: "Chart Renderer", description: "Generate visual charts and graphs for reports", subNeeds: [] }] },
    ],
    competitor: [
      { name: "Price Scraper", description: "Automated extraction of competitor pricing data", subNeeds: [{ name: "Proxy Rotator", description: "Rotate IP addresses to avoid rate limiting", subNeeds: [] }, { name: "DOM Parser", description: "Robust HTML parsing for dynamic pricing elements", subNeeds: [] }] },
      { name: "Sentiment Analyzer", description: "Analyze social media and review sentiment about competitors", subNeeds: [{ name: "NLP Pipeline", description: "Natural language processing for sentiment scoring", subNeeds: [] }] },
      { name: "Change Detector", description: "Detect and alert on competitor website changes", subNeeds: [{ name: "Diff Engine", description: "Compare page snapshots to identify changes", subNeeds: [] }, { name: "Screenshot Capture", description: "Automated full-page screenshots for visual comparison", subNeeds: [] }] },
      { name: "Strategy Mapper", description: "Map competitor movements to strategic implications", subNeeds: [{ name: "Knowledge Graph", description: "Graph database of competitive relationships and moves", subNeeds: [] }] },
    ],
    customer: [
      { name: "Lead Scorer", description: "Score and prioritize leads based on engagement signals", subNeeds: [{ name: "Behavioral Tracker", description: "Track user interactions across touchpoints", subNeeds: [] }] },
      { name: "Email Automator", description: "Personalized email sequences based on lead stage", subNeeds: [{ name: "Template Engine", description: "Dynamic email template generation with personalization tokens", subNeeds: [] }, { name: "Deliverability Monitor", description: "Track email delivery, open, and click rates", subNeeds: [] }] },
      { name: "CRM Sync", description: "Bidirectional synchronization with CRM systems", subNeeds: [{ name: "API Adapter", description: "Abstract API layer for multiple CRM providers", subNeeds: [] }] },
    ],
    content: [
      { name: "Topic Researcher", description: "AI-powered research on trending topics and keywords", subNeeds: [{ name: "Trend Analyzer", description: "Analyze search trends and social media buzz", subNeeds: [] }] },
      { name: "Content Writer", description: "Generate long-form content from research briefs", subNeeds: [{ name: "Style Adapter", description: "Match writing style to brand voice guidelines", subNeeds: [] }] },
      { name: "SEO Optimizer", description: "Automatic on-page SEO optimization", subNeeds: [{ name: "Keyword Extractor", description: "Extract and rank target keywords for content", subNeeds: [] }, { name: "Meta Generator", description: "Generate title tags and meta descriptions", subNeeds: [] }] },
      { name: "Publisher", description: "Multi-channel content publishing and scheduling", subNeeds: [{ name: "Format Converter", description: "Convert content to platform-specific formats", subNeeds: [] }] },
    ],
    code: [
      { name: "Code Generator", description: "Generate boilerplate and business logic code", subNeeds: [{ name: "AST Parser", description: "Abstract syntax tree parsing for code analysis", subNeeds: [] }] },
      { name: "Test Writer", description: "Automatic unit and integration test generation", subNeeds: [{ name: "Coverage Analyzer", description: "Track and report code coverage metrics", subNeeds: [] }] },
      { name: "Dependency Manager", description: "Monitor and update project dependencies", subNeeds: [{ name: "Vulnerability Scanner", description: "Scan dependencies for known security issues", subNeeds: [] }] },
      { name: "Documentation Builder", description: "Auto-generate API docs from code comments", subNeeds: [{ name: "Type Extractor", description: "Extract TypeScript types for documentation", subNeeds: [] }] },
    ],
  };

  // Find matching pool or use default
  let pool: Need[] = [];
  for (const [key, needs] of Object.entries(needPools)) {
    if (taskLower.includes(key)) {
      pool = needs;
      break;
    }
  }

  if (pool.length === 0) {
    pool = [
      { name: "Data Collector", description: "Gather and normalize input data from all relevant sources", subNeeds: [{ name: "API Connector", description: "Authenticate and connect to external APIs", subNeeds: [] }, { name: "Schema Mapper", description: "Map external data schemas to internal format", subNeeds: [] }] },
      { name: "Logic Processor", description: "Core business logic and computation engine", subNeeds: [{ name: "Rule Engine", description: "Configurable rules and decision tree processor", subNeeds: [] }] },
      { name: "Output Formatter", description: "Format and deliver results to appropriate channels", subNeeds: [{ name: "Template Renderer", description: "Render output using customizable templates", subNeeds: [] }] },
      { name: "Quality Validator", description: "Validate outputs against quality and accuracy standards", subNeeds: [{ name: "Test Runner", description: "Execute automated validation tests", subNeeds: [] }] },
    ];
  }

  // Return requested count (or all if less available)
  return pool.slice(0, Math.min(count, pool.length));
}

// ─── tRPC Router ───

export const genesisRouter = createRouter({
  seed: publicQuery
    .input(
      z.object({
        task: z.string().min(1, "Task description is required"),
        maxDepth: z.number().min(1).max(5).default(2),
        branchingFactor: z.number().min(1).max(6).default(3),
        enableMeta: z.boolean().default(true),
      })
    )
    .mutation(async ({ input }) => {
      const result = await simulateGenesis(input);
      return result;
    }),

  reset: publicQuery.mutation(async () => {
    // Delete all genesis data in correct order (respect FKs)
    const db = getDb();
    await db.delete(modificationLogs);
    await db.delete(agentRelationships);
    await db.delete(tasks);
    await db.delete(capabilities);
    await db.delete(agents);

    return { success: true, message: "Genesis engine reset. All agents and capabilities cleared." };
  }),

  stats: publicQuery.query(async () => {
    const db = getDb();
    const allAgents = await db.query.agents.findMany();
    const allCapabilities = await db.query.capabilities.findMany();
    const allTasks = await db.query.tasks.findMany();
    const allLogs = await db.query.modificationLogs.findMany();

    return {
      totalAgents: allAgents.length,
      totalCapabilities: allCapabilities.length,
      totalTasks: allTasks.length,
      totalLogs: allLogs.length,
      maxDepth: allAgents.reduce((max, a) => Math.max(max, a.depth), 0),
      activeAgents: allAgents.filter(
        (a) => a.status === "running" || a.status === "building"
      ).length,
      typeBreakdown: {
        root: allAgents.filter((a) => a.agentType === "root").length,
        worker: allAgents.filter((a) => a.agentType === "worker").length,
        manager: allAgents.filter((a) => a.agentType === "manager").length,
        meta: allAgents.filter((a) => a.agentType === "meta").length,
      },
    };
  }),
});
