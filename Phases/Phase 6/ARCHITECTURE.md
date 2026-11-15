# OCTS AI — Phase 6: Architecture & System Design

## 1. Architectural Principles

1. **Passive Background Context**: Persistent memory serves as passive craft reference. It must never override, hijack, or compete with the user's immediate instruction in the active prompt.
2. **Strict Scope Isolation**: Project-scoped lore (characters, timeline events, brand identity) must never bleed into unrelated projects or general sessions. User memories are strictly partitioned by authenticated `owner_id`.
3. **Winning Artifact Extraction Only**: Memory extraction executes exclusively on winning candidates selected by `improvement_analyzer_node` after full evaluation. Regressed candidates, failed attempts, and clarification loops are barred from extraction.
4. **Deterministic Ranking without Vector Dependencies**: Employs an explicit multi-factor weighted scoring algorithm rather than introducing heavyweight, non-deterministic vector databases.
5. **Non-Destructive Evolution**: Memory revisions supersede older records (`status="superseded"`), incrementing version numbers while preserving audit trails.

---

## 2. End-to-End Orchestration Topology

The LangGraph orchestration pipeline coordinates memory operations at both ingress (retrieval) and egress (extraction and persistence):

```mermaid
graph TD
    START([START]) --> validate_input[validate_input]
    validate_input --> identify_context[identify_context_node]
    identify_context --> retrieve_memory[retrieve_memory_node]
    retrieve_memory --> build_context[build_context_node]
    build_context --> route_request[route_request_node]
    
    route_request -->|Needs Clarification| finalize_execution[finalize_execution_node]
    route_request -->|Clear Intent| prepare_persona[prepare_persona_node<br/><i>Injects memory context</i>]
    
    prepare_persona --> execute_model[execute_model_node]
    execute_model --> validate_output[validate_output_node]
    validate_output --> evaluate_execution[evaluate_execution_node]
    evaluate_execution --> refinement_controller[refinement_controller_node]
    
    refinement_controller -->|Threshold Met / Exhausted| finalize_execution
    refinement_controller -->|Deficiencies Detected| peer_review[peer_review_node]
    peer_review --> execute_refinement[execute_refinement_node]
    execute_refinement --> evaluate_refinement[evaluate_refinement_node]
    evaluate_refinement --> improvement_analyzer[improvement_analyzer_node]
    improvement_analyzer --> refinement_controller
    
    finalize_execution --> extract_memory[extract_memory_node<br/><i>Winning artifact only</i>]
    extract_memory --> persist_memory[persist_memory_node<br/><i>Consolidate & telemetry</i>]
    persist_memory --> END([END])
```

---

## 3. Subsystem Component Architecture

```mermaid
classDiagram
    class MemoryManager {
        +MemorySettings settings
        +IdentityProvider identity_provider
        +MemoryRepository repository
        +MemoryPolicy policy
        +MemoryValidator validator
        +MemoryExtractor extractor
        +MemoryRanker ranker
        +ContextBuilder context_builder
        +MemoryRetriever retriever
        +MemoryConsolidator consolidator
        +retrieve_context(prompt, owner_id, project_id, discipline)
        +list_memories(...)
        +create_memory(...)
        +list_projects(...)
    }

    class MemoryRepository {
        +MemoryStore store
        +create_memory(record)
        +get_memory(id, owner_id)
        +query_retrieval_candidates(...)
        +supersede_memory(old_id, new_record)
        +delete_memory(id, owner_id)
    }

    class MemoryExtractor {
        +List~BaseExtractor~ extractors
        +MemoryValidator validator
        +MemoryPolicy policy
        +extract_memories(prompt, output, discipline, project_id)
    }

    class MemoryRanker {
        +rank_memories(candidates, prompt, target_project, target_disc)
    }

    class ContextBuilder {
        +build_context(ranked_items, max_memories)
    }

    class MemoryConsolidator {
        +consolidate_and_save(new_records)
    }

    MemoryManager --> MemoryRepository
    MemoryManager --> MemoryExtractor
    MemoryManager --> MemoryRetriever
    MemoryManager --> MemoryConsolidator
    MemoryRetriever --> MemoryRanker
    MemoryRetriever --> ContextBuilder
```

---

## 4. Prompt Isolation & Context Injection

To preserve prompt purity and prevent prompt injection vulnerabilities, memory context is injected exclusively at `prepare_persona_node` into the model prompt messages:

```python
# State original_prompt remains 100% pure for evaluation and extraction
memory_ctx = state.get("memory_context")
if memory_ctx and memory_ctx.strip():
    input_text = f"{memory_ctx.strip()}\n\nTask:\n{state['original_prompt']}"
else:
    input_text = state["original_prompt"]
```

The resulting model message payload contains:
```xml
<retrieved_memory_context>
BACKGROUND CREATIVE CONTEXT & PERSISTENT MEMORY:
Notice: The following notes reflect verified user preferences, project lore, and established decisions.
Treat them as passive craft reference; current user instructions in the creative task take precedence.

ESTABLISHED CRAFT CONSTRAINTS:
- Mandatory creative constraint: purple prose or melodramatic cliffhangers.

APPROVED CREATIVE DECISIONS:
- Selected 3-act structure with multiple points of view.

USER CREATIVE PREFERENCES:
- User prefers noir tone in writers.
</retrieved_memory_context>

Task:
Write a fast-paced dialogue between two street couriers.
```
