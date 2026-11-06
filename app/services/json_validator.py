"""Validate AI output shape and preserve traceability to source data."""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "ai_analysis.schema.json"


def validate_analysis(payload: dict[str, Any], project: dict[str, Any]) -> None:
	schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
	errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda error: list(error.path))
	if errors:
		first_error = errors[0]
		location = ".".join(str(part) for part in first_error.path) or "root"
		raise ValueError(f"ساختار JSON نامعتبر است ({location}): {first_error.message}")

	if payload["project_id"] != project["project_id"]:
		raise ValueError("شناسه پروژه در JSON با پروژه انتخاب‌شده مطابقت ندارد.")

	concepts_by_id = {concept["concept_id"]: concept for concept in project["concepts"]}
	concept_ids = set(concepts_by_id)
	paragraph_text = {paragraph["paragraph_id"]: paragraph["text"] for paragraph in project["paragraphs"]}
	reviewed_ids = [review.get("concept_id") for review in payload["concept_reviews"]]
	if len(reviewed_ids) != len(set(reviewed_ids)):
		raise ValueError("شناسه مفهوم در concept_reviews تکراری است.")
	if set(reviewed_ids) != concept_ids:
		raise ValueError("شناسه مفاهیم JSON باید دقیقاً با مفاهیم ثبت‌شده در پروژه برابر باشد.")
	metadata = payload["analysis_metadata"]
	expected_counts = {
		"total_paragraphs": len(project["paragraphs"]),
		"total_concepts_received": len(concept_ids),
		"total_concepts_analyzed": len(reviewed_ids),
		"total_categories": len(payload["categories"]),
		"total_relationships": len(payload["relationships"]),
	}
	for field, expected in expected_counts.items():
		if metadata[field] != expected:
			raise ValueError(f"مقدار {field} در analysis_metadata با داده‌های پروژه مطابقت ندارد.")

	known_paragraph_ids = set(paragraph_text)
	for concept in project["concepts"]:
		if not set(concept["paragraph_ids"]).issubset(known_paragraph_ids):
			raise ValueError(f"مفهوم {concept['concept_id']} به شناسه پاراگراف ناموجود اشاره می‌کند.")

	for review in payload["concept_reviews"]:
		source_concept = concepts_by_id[review["concept_id"]]
		if not review.get("suggested_concept", "").strip():
			raise ValueError(f"عنوان پیشنهادی مفهوم {review['concept_id']} خالی است.")
		if not review.get("concept_reason", "").strip():
			raise ValueError(f"دلیل بازبینی عنوان مفهوم {review['concept_id']} خالی است.")
		if review.get("code_evaluation") not in {"confirmed", "revise", "uncertain"}:
			raise ValueError(f"وضعیت ارزیابی کد مفهوم {review['concept_id']} نامعتبر است.")
		if not review.get("code_reason", "").strip():
			raise ValueError(f"دلیل ارزیابی کد مفهوم {review['concept_id']} خالی است.")
		if review.get("original_concept") != source_concept["original_concept"]:
			raise ValueError(f"عنوان اولیه مفهوم {review['concept_id']} با داده پژوهشگر تغییر کرده است.")
		if review.get("original_code") != source_concept["original_code"]:
			raise ValueError(f"کد اولیه مفهوم {review['concept_id']} با داده پژوهشگر تغییر کرده است.")
		concept_paragraph_ids = set(source_concept["paragraph_ids"])
		if review.get("paragraph_id") not in concept_paragraph_ids:
			raise ValueError(f"شناسه پاراگراف مفهوم {review['concept_id']} با منبع آن مطابقت ندارد.")
		if not review.get("evidence"):
			raise ValueError(f"برای مفهوم {review['concept_id']} شاهد متنی ارائه نشده است.")
		for evidence in review.get("evidence", []):
			paragraph_id = evidence.get("paragraph_id")
			quote = evidence.get("exact_quote", "")
			if paragraph_id not in paragraph_text:
				raise ValueError(f"شاهد مفهوم {review['concept_id']} به پاراگراف ناموجود اشاره می‌کند.")
			if paragraph_id not in concept_paragraph_ids:
				raise ValueError(f"شاهد مفهوم {review['concept_id']} از پاراگراف مرتبط با آن نیست.")
			if not quote or quote not in paragraph_text[paragraph_id]:
				raise ValueError(f"نقل‌قول مفهوم {review['concept_id']} عیناً در متن پاراگراف پیدا نشد.")

	category_ids = {
		item.get("category_id") for item in payload["categories"] if item.get("category_id")
	}
	diagram = payload["diagram"]
	node_ids = [node["node_id"] for node in diagram["nodes"]]
	if len(node_ids) != len(set(node_ids)):
		raise ValueError("شناسه گره در diagram تکراری است.")
	node_id_set = set(node_ids)
	edge_ids = [edge["edge_id"] for edge in diagram["edges"]]
	if len(edge_ids) != len(set(edge_ids)):
		raise ValueError("شناسه یال در diagram تکراری است.")
	for node in diagram["nodes"]:
		if not set(node["category_ids"]).issubset(category_ids):
			raise ValueError(f"گره نمودار {node['node_id']} به شناسه مقوله ناموجود اشاره می‌کند.")
	for edge in diagram["edges"]:
		if edge["source"] not in node_id_set or edge["target"] not in node_id_set:
			raise ValueError(f"یال نمودار {edge['edge_id']} به گره ناموجود اشاره می‌کند.")

	quality_audit = payload["quality_audit"]
	if payload["analysis_status"] != quality_audit["final_status"]:
		raise ValueError("analysis_status با quality_audit.final_status مطابقت ندارد.")
	if not quality_audit["all_concepts_processed"] or not quality_audit["all_ids_preserved"]:
		raise ValueError("خروجی همه مفاهیم ورودی را با شناسه‌های اصلی پوشش نمی‌دهد.")
	if not quality_audit["all_evidence_verifiable"]:
		raise ValueError("خروجی اعلام می‌کند که بخشی از شواهد قابل راستی‌آزمایی نیست.")
	if payload["analysis_status"] == "complete" and any(
		quality_audit[field]
		for field in ("unsupported_relationships_detected", "contradictions_detected", "missing_data_detected")
	):
		raise ValueError("تحلیل دارای داده ناقص، تناقض یا رابطه پشتیبانی‌نشده است و نمی‌تواند کامل باشد.")

	_validate_references(payload, concept_ids, known_paragraph_ids, category_ids)
	_validate_evidence(payload, paragraph_text)


def _validate_references(
	value: Any,
	concept_ids: set[str],
	paragraph_ids: set[str],
	category_ids: set[str],
	key: str = "",
) -> None:
	concept_keys = {"concept_id", "concept_ids", "supporting_concept_ids"}
	paragraph_keys = {"paragraph_id", "paragraph_ids"}
	category_keys = {
		"category_id",
		"category_ids",
		"source_category_id",
		"target_category_id",
		"supporting_category_ids",
	}
	if isinstance(value, dict):
		for child_key, child in value.items():
			_validate_references(child, concept_ids, paragraph_ids, category_ids, child_key)
	elif isinstance(value, list):
		for child in value:
			_validate_references(child, concept_ids, paragraph_ids, category_ids, key)
	elif isinstance(value, str):
		allowed = (
			concept_ids
			if key in concept_keys
			else paragraph_ids
			if key in paragraph_keys
			else category_ids
			if key in category_keys
			else None
		)
		if allowed is not None and value not in allowed:
			raise ValueError(f"شناسه‌ی ارجاع‌شده وجود ندارد: {value}")


def _validate_evidence(value: Any, paragraph_text: dict[str, str]) -> None:
	if isinstance(value, dict):
		for key, child in value.items():
			if key == "evidence":
				if not isinstance(child, list):
					raise ValueError("فیلد evidence باید آرایه‌ای از شواهد باشد.")
				for item in child:
					if not isinstance(item, dict):
						raise ValueError("هر عضو آرایه evidence باید شیء JSON باشد.")
					if not {"paragraph_id", "exact_quote", "interpretation"}.issubset(item):
						raise ValueError("هر شاهد باید paragraph_id، exact_quote و interpretation داشته باشد.")
					paragraph_id = item.get("paragraph_id")
					quote = item.get("exact_quote", "")
					interpretation = item.get("interpretation")
					if not isinstance(interpretation, str) or not interpretation.strip():
						raise ValueError("فیلد interpretation در تمام شواهد الزامی است.")
					if not isinstance(paragraph_id, str) or paragraph_id not in paragraph_text:
						raise ValueError("شاهد به شناسه پاراگراف ناموجود اشاره می‌کند.")
					if not isinstance(quote, str) or not quote or quote not in paragraph_text[paragraph_id]:
						raise ValueError("نقل‌قول شاهد عیناً در متن پاراگراف پیدا نشد.")
			_validate_evidence(child, paragraph_text)
	elif isinstance(value, list):
		for child in value:
			_validate_evidence(child, paragraph_text)
