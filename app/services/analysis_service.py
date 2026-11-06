"""Coordinate prompt preparation and imported AI results.

Qualitative interpretation is performed by the external AI workflow and reviewed
by the researcher; this service does not independently code interview data.
"""

import json
from typing import Any

from app.services.json_validator import validate_analysis
from app.services.prompt_builder import build_prompt


def prepare_prompt(project: dict[str, Any]) -> str:
	return build_prompt(project)


def prepare_analysis_results(data: dict[str, Any]) -> dict[str, Any]:
	"""Map validated AI output into explicit sections consumed by result pages."""
	concept_rows = [
		{
			"concept_id": item.get("concept_id", ""),
			"paragraph_id": item.get("paragraph_id", ""),
			"original_concept": item.get("original_concept", ""),
			"suggested_concept": item.get("suggested_concept", ""),
			"concept_change_required": item.get("concept_change_required", False),
			"concept_reason": item.get("concept_reason", ""),
			"original_code": item.get("original_code", ""),
			"suggested_code": item.get("suggested_code", ""),
			"code_evaluation": item.get("code_evaluation", ""),
			"code_reason": item.get("code_reason", ""),
			"evidence": item.get("evidence", []),
			"confidence": item.get("confidence", 0),
			"needs_researcher_review": item.get("needs_researcher_review", True),
		}
		for item in data.get("concept_reviews", [])
	]
	return {
		"concept_rows": concept_rows,
		"categories": data.get("categories", []),
		"central_phenomenon": data.get("central_phenomenon"),
		"paradigm_model": data.get("paradigm_model", {}),
		"relationships": data.get("relationships", []),
		"diagram": data.get("diagram", {"nodes": [], "edges": []}),
		"researcher_review": data.get("researcher_review", []),
		"quality_audit": data.get("quality_audit", {}),
		"analysis_metadata": data.get("analysis_metadata", {}),
		"analysis_status": data.get("analysis_status", "incomplete"),
	}


def parse_analysis_json(raw_json: str, project: dict[str, Any]) -> dict[str, Any]:
	try:
		payload = json.loads(raw_json)
	except json.JSONDecodeError as error:
		raise ValueError(f"JSON معتبر نیست: {error.msg} (سطر {error.lineno})") from error
	if not isinstance(payload, dict):
		raise ValueError("ریشه‌ی JSON باید یک شیء باشد.")
	validate_analysis(payload, project)
	return payload
