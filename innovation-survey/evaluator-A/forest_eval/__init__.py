"""forest_eval: an evaluator-first toolkit for forestry / environmental ML.

评估器优先：先把"怎么算分"钉死，再让任何搜索（人、脚本、LLM 代理）去找答案。
Evaluator-first: pin down *how answers are scored* before letting any searcher
(human, script or LLM agent) look for answers.
"""

from .evaluator import ForestEvaluator, EvalResult
from .data import load_covertype, CovertypeSplits

__all__ = ["ForestEvaluator", "EvalResult", "load_covertype", "CovertypeSplits"]
