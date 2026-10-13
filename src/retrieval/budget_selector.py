"""Budget-Aware Context Selection & Multi-Strategy Retrieval Engine.

Implements and benchmarks three retrieval paradigms:
1. Lexical / Keyword BM25 / Token Overlap
2. Dense Embedding (TF-IDF Cosine Similarity)
3. Budget-Aware Graph-Guided Repair (BAGR) Retrieval
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from src.graph.repo_graph import RepoGraph


@dataclass
class RetrievedSnippet:
    entity_id: str
    name: str
    entity_type: str
    filepath: str
    start_line: int
    end_line: int
    source_code: str
    score: float
    token_count: int
    retrieval_mode: str


def estimate_tokens(text: str) -> int:
    """Fast, accurate approximation of token count for code and natural language.
    On BPE tokenizers (Gemma / Llama), 1 token ~ 3.6 to 4 characters.
    """
    if not text:
        return 0
    # Words + symbols rough heuristic
    words = len(re.findall(r"\w+|[^\w\s]", text))
    char_estimate = len(text) / 3.8
    return max(1, int(math.ceil((words + char_estimate) / 2)))


class BudgetSelector:
    """Performs ranked retrieval and knapsack context packing under a hard token budget."""

    def __init__(self, repo_graph: RepoGraph, max_tokens: int = 2048):
        self.repo_graph = repo_graph
        self.max_tokens = max_tokens
        self.nodes_data = dict(repo_graph.graph.nodes(data=True))

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase alphanumeric tokens split by underscore or camelCase
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return [w for w in words if len(w) > 1]

    def _lexical_similarity(self, query_tokens: List[str], text: str) -> float:
        if not text:
            return 0.0
        doc_tokens = set(self._tokenize(text))
        if not doc_tokens:
            return 0.0
        overlap = sum(1 for q in query_tokens if q in doc_tokens)
        return overlap / math.sqrt(len(doc_tokens) + 1.0)

    def retrieve_keyword_only(self, query: str, token_budget: Optional[int] = None) -> List[RetrievedSnippet]:
        """Baseline 1: Pure lexical keyword match without graph topology."""
        budget = token_budget or self.max_tokens
        q_tokens = self._tokenize(query)
        scored: List[Tuple[str, float]] = []

        for node_id, data in self.nodes_data.items():
            if data.get("entity_type") == "file":
                continue  # Prefer function/class granular entities
            content = f"{data.get('name', '')} {data.get('docstring', '')} {data.get('source_code', '')}"
            score = self._lexical_similarity(q_tokens, content)
            if score > 0:
                scored.append((node_id, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return self._pack_budget(scored, budget, mode="keyword_only")

    def retrieve_dense_embedding(self, query: str, token_budget: Optional[int] = None) -> List[RetrievedSnippet]:
        """Baseline 2: Dense / TF-IDF Vector Space similarity without graph topology."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        budget = token_budget or self.max_tokens
        node_ids: List[str] = []
        corpus: List[str] = []

        for node_id, data in self.nodes_data.items():
            if data.get("entity_type") == "file":
                continue
            text = f"{data.get('name', '')} {data.get('docstring', '')} {data.get('source_code', '')}"
            if text.strip():
                node_ids.append(node_id)
                corpus.append(text)

        if not corpus:
            return []

        vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
            q_vec = vectorizer.transform([query])
            sims = cosine_similarity(q_vec, tfidf_matrix).flatten()
            scored = [(node_ids[i], float(sims[i])) for i in range(len(node_ids)) if sims[i] > 0.01]
            scored.sort(key=lambda x: x[1], reverse=True)
        except Exception:
            return self.retrieve_keyword_only(query, budget)

        return self._pack_budget(scored, budget, mode="dense_embedding")

    def retrieve_graph_guided(
        self,
        query: str,
        token_budget: Optional[int] = None,
        alpha_lexical: float = 0.45,
        graph_hops: int = 2,
    ) -> List[RetrievedSnippet]:
        """Proposed BAGR: Hybrid Lexical Seed + Graph Personalized PageRank + Knapsack Packing."""
        budget = token_budget or self.max_tokens
        q_tokens = self._tokenize(query)

        # 1. Discover Initial Seed Nodes (Top Lexical Matches)
        seed_candidates: List[Tuple[str, float]] = []
        for node_id, data in self.nodes_data.items():
            content = f"{data.get('name', '')} {data.get('docstring', '')}"
            score = self._lexical_similarity(q_tokens, content)
            if score > 0:
                seed_candidates.append((node_id, score))

        seed_candidates.sort(key=lambda x: x[1], reverse=True)
        seeds = [n for n, _ in seed_candidates[:5]]

        # 2. Personalized PageRank + Neighborhood Proximity
        ppr_scores = self.repo_graph.personalized_pagerank(seeds, alpha=0.85)
        k_neighborhood = self.repo_graph.get_k_hop_neighborhood(seeds, k=graph_hops)

        # 3. Composite Fusion Scoring
        final_scores: List[Tuple[str, float]] = []
        for node_id, data in self.nodes_data.items():
            if data.get("entity_type") == "file":
                continue  # Prefer function/class entities
            lex_score = self._lexical_similarity(
                q_tokens, f"{data.get('name', '')} {data.get('docstring', '')} {data.get('source_code', '')}"
            )
            graph_score = ppr_scores.get(node_id, 0.0)
            bonus = 0.2 if node_id in k_neighborhood else 0.0

            composite = (alpha_lexical * lex_score) + ((1.0 - alpha_lexical) * graph_score * 10.0) + bonus
            if composite > 0.01:
                final_scores.append((node_id, composite))

        final_scores.sort(key=lambda x: x[1], reverse=True)
        return self._pack_budget(final_scores, budget, mode="bagr_graph_guided")

    def _pack_budget(
        self,
        ranked_nodes: List[Tuple[str, float]],
        budget: int,
        mode: str,
    ) -> List[RetrievedSnippet]:
        """Greedy knapsack context packing under hard token ceiling."""
        retrieved: List[RetrievedSnippet] = []
        current_tokens = 0

        for node_id, score in ranked_nodes:
            data = self.nodes_data.get(node_id)
            if not data:
                continue

            source = data.get("source_code", "")
            if not source.strip():
                continue

            node_tokens = estimate_tokens(source)
            if current_tokens + node_tokens > budget:
                # If cannot fit full body, check if signature + docstring can fit
                sig_doc = f"# {data.get('name', '')}\n\"\"\"{data.get('docstring', '')}\"\"\"\n    # [Implementation truncated by budget controller]"
                sig_tokens = estimate_tokens(sig_doc)
                if current_tokens + sig_tokens <= budget:
                    source = sig_doc
                    node_tokens = sig_tokens
                else:
                    continue

            snippet = RetrievedSnippet(
                entity_id=node_id,
                name=data.get("name", ""),
                entity_type=data.get("entity_type", "function"),
                filepath=data.get("filepath", ""),
                start_line=data.get("start_line", 1),
                end_line=data.get("end_line", 1),
                source_code=source,
                score=round(score, 4),
                token_count=node_tokens,
                retrieval_mode=mode,
            )
            retrieved.append(snippet)
            current_tokens += node_tokens

            if current_tokens >= budget:
                break

        return retrieved

    def format_context_prompt(self, snippets: List[RetrievedSnippet]) -> str:
        """Formats retrieved code snippets into a markdown code block for LLM prompt."""
        if not snippets:
            return "No relevant code context discovered."

        blocks = []
        for s in snippets:
            blocks.append(
                f"### Entity: `{s.name}` ({s.entity_type})\n"
                f"File: `{s.filepath}` (Lines {s.start_line}-{s.end_line}) | Score: {s.score}\n"
                f"```python\n{s.source_code}\n```"
            )
        return "\n\n".join(blocks)
