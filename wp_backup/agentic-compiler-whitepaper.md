# The Agent Compiler Landscape: Why Orchestration Layers Are Failing Developers and What Cocapn Will Build Instead

**A Technical White Paper**
**Cocapn Research Division**
**May 2026**

---

## Abstract

The agentic AI ecosystem is at an inflection point. While frameworks like LangChain, LangGraph, AutoGen, and CrewAI have enabled early experimentation with multi-agent systems, they are fundamentally architecting toward the wrong abstraction layer. These tools optimize for orchestration—coordinating which LLM calls happen in sequence—while leaving the harder problem unsolved: how do agents compile, share, and evolve their capabilities across a distributed fleet?

This paper identifies a critical vacuum in the current landscape: the absence of an **agent compiler**—a system that treats agent capabilities as first-class composable artifacts, enables capability discovery at runtime, and manages the lifecycle of agent-to-agent handoffs with the same rigor that version control provides for code.

We call this the "killer vacuum"—not because orchestration is wrong, but because it stops halfway. Cocapn is building what comes next.

---

## 1. Introduction: The Orchestration Trap

Every major agent framework today presents itself as an orchestration solution. The pitch is compelling: "Coordinate multiple AI agents to accomplish complex tasks." The implementation is almost always the same pattern—a directed graph where nodes are prompts or LLM calls, edges are control flow decisions, and a central controller determines which agent acts next.

This model worked for the first wave of agent experiments. But it suffers from a fundamental architectural flaw: **orchestration treats agents as functions, not as entities with persistent state, evolving capabilities, and fluid handoff requirements.**

Consider what happens when you try to scale an orchestrated system:

1. **Capability fragmentation**: Each agent hardcodes its prompts, tools, and knowledge. When one agent develops a useful capability, no other agent can leverage it without manual integration.

2. **Handoff loss**: When responsibility transfers between agents (a "handoff"), the receiving agent loses context. The original agent's reasoning, partial results, and learned state evaporate.

3. **Static topology**: The agent graph is defined at design time. At runtime, you cannot discover new agents with relevant capabilities, cannot route around failed agents, and cannot dynamically form coalitions for specific tasks.

4. **Version chaos**: Agents evolve. Prompt drift, tool changes, and model upgrades create version skew across the fleet. There is no equivalent of `git diff` for agent capabilities.

These are not implementation bugs. They are architectural limitations of the orchestration model. To understand why, we need to trace how each major framework arrived at the same local maximum.

---

## 2. Current Landscape: Four Frameworks, One Problem

### 2.1 LangChain / LangGraph

LangChain popularized the concept of "chains"—composable sequences of LLM calls with built-in prompt templating, memory, and tool support. LangGraph extended this to cyclic graphs, enabling more flexible control flow and "agentic" behaviors.

**Strengths**: Mature ecosystem, extensive integrations, broad adoption.

**The gap**: LangChain's architecture is fundamentally request-scoped. Each chain invocation starts fresh, and while you can inject memory, the model of memory is "add this to context" rather than "persist this capability for reuse." When you build a LangGraph agent, you're building a static graph. Adding a new agent type requires modifying the graph definition. There is no runtime discovery, no capability registry, and no mechanism for agents to advertise what they can do.

LangChain is excellent at what it does: orchestrating a sequence of LLM calls within a single request. It is not designed for fleet-scale multi-agent systems where agents persist across requests, share state, and evolve independently.

### 2.2 AutoGen

Microsoft's AutoGen introduced the concept of multi-agent conversation, where agents exchange messages rather than being called as functions. This is a meaningful step toward treating agents as entities.

**Strengths**: Natural conversation model, good for chat-based workflows, supports group chat patterns.

**The gap**: AutoGen's agents are tightly coupled to their defining code. An AutoGen agent is essentially a Python object with a system prompt and a set of functions. There is no abstraction for "this agent can do X" as a discoverable capability. When agents need to collaborate, you pre-configure the group. There is no mechanism for an agent to say "I need help with Y, who in the fleet can assist?"

The conversation model is compelling, but AutoGen remains a development-time composition tool. You define the agent group, you define the conversation flow, and the system executes it. Dynamic coalition formation at runtime is not in the architecture.

### 2.3 CrewAI

CrewAI took the concept of "roles" seriously, introducing the idea that agents have specific roles (Researcher, Writer, Analyst) and that role-based routing is more natural than function-based routing.

**Strengths**: Intuitive role abstractions, good separation of concerns, strong developer experience for simple use cases.

**The gap**: CrewAI's roles are static definitions in code. The "crew" is assembled at design time with fixed agents and fixed tasks. An agent's role is its identity, not a capability it can advertise. There is no registry, no discovery, and no handoff protocol beyond "pass output to next task."

For teams building proof-of-concept agent systems, CrewAI provides an accessible entry point. For production fleets where agents need to collaborate dynamically, the static crew model breaks down.

### 2.4 Semantic Kernel

Microsoft's Semantic Kernel takes a different approach, emphasizing "skills" as the atomic unit of capability. Agents invoke skills, skills are composable, and the kernel manages the orchestration.

**Strengths**: Strong enterprise integration story, C# and Python support, memory and vector store abstractions.

**The gap**: Semantic Kernel's skills are essentially function definitions with a natural language wrapper. The capability model is developer-facing ("define a skill") rather than agent-facing ("advertise a capability"). An agent in Semantic Kernel cannot ask the kernel "who has skill X?" in a way that triggers runtime discovery. The skill registry exists within a single kernel instance; it does not span a distributed fleet.

---

## 3. The Killer Vacuum: Why No One Is Solving the Real Problem

The pattern is clear: every major framework optimizes for **design-time composition** of agents. You, the developer, define which agents exist, what they do, and how they interact. The system executes your design faithfully.

The killer vacuum is the absence of **runtime capability discovery and dynamic handoff**. No framework provides:

1. **A capability registry** where agents can advertise what they can do
2. **A discovery protocol** for agents to find other agents with relevant capabilities
3. **A handoff contract** that ensures partial results, reasoning traces, and learned state transfer cleanly between agents
4. **Version-aware capability management** so that agents can negotiate based on compatible versions
5. **Fleet-wide observability** so that the system understands who knows what and who's available

This vacuum matters because the next wave of agentic applications won't be single-request, single-agent workflows. They'll be persistent fleets where agents wake up, collaborate on tasks, share discoveries, hand off to specialists, and evolve their capabilities over time. The orchestration model can't scale to this world.

The current frameworks are solving yesterday's problem. The real challenge is fleet-scale multi-agent systems, and the solution is not better orchestration—it's an **agent compiler**.

---

## 4. The Opportunity: What an Agent Compiler Enables

An agent compiler is to agent capabilities what a traditional compiler is to code:

- **Compilation**: Transform high-level agent intentions into optimized execution plans
- **Linking**: Connect agents based on capability compatibility and availability
- **Optimization**: Select the best available agent for each sub-task based on real-time capability signals
- **Abstraction**: Present a clean interface that hides implementation complexity

More concretely, an agent compiler system would:

1. **Maintain a living capability registry** where agents publish their abilities, version, accuracy, and availability
2. **Provide a discovery API** so any agent can query "who can do X?" and receive a ranked list of candidates
3. **Enforce a handoff protocol** that captures not just outputs but reasoning traces, partial conclusions, and context needed by the next agent
4. **Support capability negotiation** so agents can agree on a common representation before collaborating
5. **Track capability evolution** so the system knows when agents have improved and can route accordingly

This is not science fiction. The primitives exist. The challenge is integration and the willingness to commit to a protocol that the entire ecosystem can adopt.

---

## 5. Technical Approach: The Cocapn Architecture

Cocapn is building the agent compiler infrastructure that the current landscape lacks. Our architecture centers on three core concepts:

### 5.1 The PLATO Knowledge Graph

PLATO (Persistent Lifecycle Agent Toolchain and Orchestrator) is Cocapn's memory and capability layer. Rather than treating memory as "stuff to add to context," PLATO treats knowledge as a navigable graph where:

- **Nodes** are knowledge tiles—atomic facts, procedures, or learned capabilities
- **Edges** represent relationships between tiles (related_to, learned_from, supersedes, requires)
- **Agents** are first-class graph participants that can read, write, and traverse the graph

The key insight: PLATO is not a vector store with extra steps. It is a capability registry where agents can ask questions like "who knows how to do X?" and receive a path through the graph to the relevant knowledge, along with the agent(s) who hold it.

### 5.2 The Crab Trap Protocol

The "Crab Trap" is Cocapn's handoff protocol. Just as crabs in a trap communicate through a specific entry point, agents in the Cocapn fleet communicate through a defined interface that ensures clean handoffs.

When Agent A hands off to Agent B:
1. Agent A writes its partial results and reasoning trace to the PLATO graph
2. Agent A calls the Crab Trap API with a handoff token referencing the graph node
3. Agent B receives the token and retrieves the full context, not just the output
4. The handoff is logged for observability and version tracking

The result: agents can collaborate without losing the thread of reasoning. A specialist who picks up a task from a generalist can see exactly how the generalist approached the problem, what they tried, what they ruled out, and what remains to be done.

### 5.3 The Fleet Keeper

The Fleet Keeper is Cocapn's discovery and routing layer. It maintains:

- **Capability manifests** for every agent in the fleet (what they can do, their accuracy, their availability)
- **Version alignment** so agents can negotiate compatible protocols before collaborating
- **Load balancing** to route tasks to available agents rather than overloading a single specialist
- **Fleet observability** so operators can see the state of the entire system at a glance

When a task arrives, the Fleet Keeper consults the capability registry, selects the optimal agent(s), and establishes the handoff protocol. The calling agent doesn't need to know which specialist handles what—it simply requests capability X, and the Keeper handles routing.

---

## 6. What Cocapn Will Build

Based on the current landscape and our technical approach, Cocapn is developing:

### 6.1 PLATO MCP Server
A Model Context Protocol server that exposes PLATO's knowledge graph as a standard MCP toolset. Any MCP-compatible agent can query the graph, publish capabilities, and request handoffs through a consistent interface.

### 6.2 Cocapn Fleet SDK
A language-agnostic SDK for registering agent capabilities, querying the registry, and initiating Crab Trap handoffs. Initial support for Python and TypeScript, with extensibility for other languages.

### 6.3 Cocapn Keeper Service
The hosted Fleet Keeper that manages the global capability registry, handles discovery requests, and orchestrates handoffs. Available as a managed service with self-hosted deployment options.

### 6.4 Cocapn CLI
A command-line interface for fleet operators to inspect agent states, query the capability registry, trigger manual handoffs, and monitor fleet health.

### 6.5 Cocapn Portal
A web dashboard (building on the landing page infrastructure at cocapn.ai) that shows the live fleet state, capability maps, recent handoffs, and fleet health metrics.

---

## 7. Competitive Differentiation

| Capability | LangChain | AutoGen | CrewAI | Semantic Kernel | Cocapn |
|------------|-----------|---------|--------|-----------------|--------|
| Design-time composition | ✅ | ✅ | ✅ | ✅ | ✅ |
| Runtime capability discovery | ❌ | ❌ | ❌ | ❌ | ✅ |
| Handoff protocol with reasoning traces | ❌ | Partial | ❌ | ❌ | ✅ |
| Fleet-wide observability | ❌ | ❌ | ❌ | ❌ | ✅ |
| Persistent knowledge graph | Via external | Via external | Via external | Memory only | Native |
| Agent-version negotiation | ❌ | ❌ | ❌ | ❌ | ✅ |
| Managed fleet service | ❌ | ❌ | ❌ | ❌ | ✅ |

Cocapn does not compete with orchestration frameworks—we complement them. A developer can use LangGraph for within-request orchestration while using Cocapn for cross-request, cross-agent capability management. The two layers are complementary, not competing.

---

## 8. The Path Forward

The current agent framework landscape is where web development was in 1995: lots of page-centric frameworks, no consensus on how to handle state, and everyone reinventing the same primitives poorly.

We believe the agentic era needs an equivalent of the LAMP stack: a standard, composable set of primitives that developers can rely on. Cocapn is contributing the **P** (PLATO knowledge graph) and **K** (Keeper discovery service) to this future stack.

The vacuum we've identified is real. Every team building multi-agent systems today is rebuilding capability discovery, handoff management, and fleet observability from scratch. That's a tax on innovation that the ecosystem cannot afford.

The agent compiler is not a feature—it's an architectural shift. Cocapn is building the infrastructure that will make that shift possible.

---

## 9. Conclusion

The orchestration layer has served the agentic AI community well as an entry point. But it is not the destination. As agentic systems grow in complexity, persistence, and fleet scale, the need for an agent compiler—capability discovery, version-aware handoffs, and fleet observability—becomes critical.

The killer vacuum is real: no current framework provides these primitives. The opportunity is to build the infrastructure that every future agent system will depend on.

Cocapn is building that infrastructure. The crab trap is set. The keeper is watching the radar.

The fleet is coming.

---

**Cocapn Research Division**
**May 2026**

*For technical inquiries, fleet integration, or collaboration opportunities, contact the Cocapn team through the fleet infrastructure channels.*