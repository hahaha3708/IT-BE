import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

from django.db.models import Q
from rest_framework.exceptions import ValidationError


WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
TOKEN_STOPWORDS = {"va", "and", "or", "the", "a", "an", "cho", "voi", "la", "cua", "con", "mot", "nhung"}


@dataclass(frozen=True)
class CandidateSearchParams:
	q: str = ""
	location: str = ""
	salary_min: Optional[Decimal] = None
	salary_max: Optional[Decimal] = None
	availability_slots: Tuple[str, ...] = ()
	sort: str = "matching_desc"


def parse_search_params(query_params):
	q = (query_params.get("q") or "").strip()
	location = (query_params.get("location") or "").strip()
	salary_min = _parse_decimal(query_params.get("salary_min"), "salary_min")
	salary_max = _parse_decimal(query_params.get("salary_max"), "salary_max")
	availability_slots = _parse_availability_slots(query_params.get("availability_slots"))
	sort = (query_params.get("sort") or "matching_desc").strip() or "matching_desc"
	allowed_sorts = {"matching_desc", "updated_desc"}
	if sort not in allowed_sorts:
		raise ValidationError({"sort": "Gia tri sort khong hop le."})

	return CandidateSearchParams(
		q=q,
		location=location,
		salary_min=salary_min,
		salary_max=salary_max,
		availability_slots=availability_slots,
		sort=sort,
	)


def apply_candidate_filters(queryset, params):
	if params.q:
		queryset = queryset.filter(Q(ho_ten__icontains=params.q) | Q(ky_nang__icontains=params.q))

	if params.location:
		queryset = queryset.filter(location__icontains=params.location)

	if params.salary_min is not None:
		queryset = queryset.filter(luong_mong_muon__gte=params.salary_min)

	if params.salary_max is not None:
		queryset = queryset.filter(luong_mong_muon__lte=params.salary_max)

	return queryset


def filter_candidates_by_slots(candidates, availability_slots):
	if not availability_slots:
		return list(candidates)

	target_slots = set(availability_slots)
	filtered_candidates = []
	for candidate in candidates:
		candidate_slots = set(parse_candidate_slots(candidate))
		if candidate_slots & target_slots:
			filtered_candidates.append(candidate)
	return filtered_candidates


def calculate_matching_score(candidate, params, job=None):
	target_terms = _job_terms(job) if job is not None else _query_terms(params.q)
	location_target = _job_location(job) if job is not None else params.location
	availability_target = _job_slots(job) if job is not None else set(params.availability_slots)

	skills_score = _skill_score(candidate, target_terms)
	availability_score = _availability_score(candidate, availability_target)
	location_score = _location_score(candidate, location_target)

	return round((skills_score * 50.0) + (availability_score * 30.0) + (location_score * 20.0), 1)


def sort_candidates(candidates, params):
	if params.sort == "updated_desc":
		return sorted(candidates, key=lambda item: (-_candidate_timestamp(item[0]), item[0].ung_vien_id))

	return sorted(
		candidates,
		key=lambda item: (-item[1], -_candidate_timestamp(item[0]), item[0].ung_vien_id),
	)


def parse_skill_list(raw_value):
	if not raw_value:
		return []

	if isinstance(raw_value, list):
		raw_items = raw_value
	else:
		raw_items = re.split(r"[\n,;|]+", str(raw_value))

	parsed_items = []
	for item in raw_items:
		clean_item = str(item).strip()
		if clean_item:
			parsed_items.append(clean_item)
	return parsed_items


def parse_candidate_slots(candidate):
	raw_slots = getattr(candidate, "availability_slots", None)
	if isinstance(raw_slots, list):
		return [str(slot).strip() for slot in raw_slots if str(slot).strip()]

	if raw_slots:
		return parse_skill_list(raw_slots)

	legacy_value = getattr(candidate, "thoi_gian_ranh", None)
	if legacy_value:
		try:
			loaded_value = json.loads(legacy_value)
		except (TypeError, ValueError):
			return parse_skill_list(legacy_value)
		if isinstance(loaded_value, list):
			return [str(slot).strip() for slot in loaded_value if str(slot).strip()]

	return []


def parse_decimal_value(raw_value):
	if raw_value in (None, ""):
		return None
	try:
		return Decimal(str(raw_value).strip())
	except (InvalidOperation, AttributeError, TypeError) as exc:
		raise ValidationError({"salary": "Must be a valid number"}) from exc


def decimal_to_number(value):
	if value is None:
		return None
	if value == value.to_integral():
		return int(value)
	return float(value)


def format_datetime(value):
	if value is None:
		return None
	formatted_value = value.isoformat()
	return formatted_value.replace("+00:00", "Z")


def build_avatar_url(candidate, request=None):
	avatar_value = getattr(candidate, "avatar", None)
	if not avatar_value:
		return None

	avatar_value = str(avatar_value)
	if avatar_value.startswith(("http://", "https://")):
		return avatar_value
	if request is not None and avatar_value.startswith("/"):
		return request.build_absolute_uri(avatar_value)
	return avatar_value


def build_review_summary(reviews):
	review_list = list(reviews)
	if not review_list:
		return {"avg_rating": 0, "total_reviews": 0}

	average_rating = sum(review.diem_so for review in review_list) / len(review_list)
	return {"avg_rating": round(float(average_rating), 1), "total_reviews": len(review_list)}


def build_review_items(reviews):
	return [
		{
			"rating": review.diem_so,
			"comment": review.nhan_xet,
			"created_at": format_datetime(review.tao_luc),
		}
		for review in reviews
	]


def candidate_has_availability_overlap(candidate, availability_slots):
	if not availability_slots:
		return True
	return bool(set(parse_candidate_slots(candidate)) & set(availability_slots))


def normalize_text(value):
	if not value:
		return ""
	normalized_value = unicodedata.normalize("NFKD", str(value))
	without_accents = "".join(character for character in normalized_value if not unicodedata.combining(character))
	return re.sub(r"\s+", " ", without_accents).strip().lower()


def candidate_sort_timestamp(candidate):
	return _candidate_timestamp(candidate)


def _parse_decimal(raw_value, field_name):
	if raw_value in (None, ""):
		return None
	try:
		return Decimal(str(raw_value).strip())
	except (InvalidOperation, AttributeError, TypeError) as exc:
		raise ValidationError({field_name: "Must be a valid number"}) from exc


def _parse_availability_slots(raw_value):
	if raw_value in (None, ""):
		return ()

	try:
		parsed_value = json.loads(raw_value)
	except (TypeError, ValueError) as exc:
		raise ValidationError({"availability_slots": "Must be a valid JSON array"}) from exc

	if not isinstance(parsed_value, list) or any(not isinstance(item, str) for item in parsed_value):
		raise ValidationError({"availability_slots": "Must be a JSON array of strings"})

	return tuple(item.strip() for item in parsed_value if item.strip())


def _query_terms(raw_value):
	return set(_tokenize(raw_value))


def _job_terms(job):
	if job is None:
		return set()
	return set(_tokenize(f"{job.tieu_de} {job.noi_dung}"))


def _job_location(job):
	if job is None:
		return ""
	return (getattr(job, "dia_diem_lam_viec", "") or "").strip()


def _job_slots(job):
	if job is None:
		return set()

	start_time = getattr(job, "bat_dau_lam", None)
	end_time = getattr(job, "ket_thuc_lam", None)
	if not start_time or not end_time:
		return set()

	return _build_slots_from_range(start_time, end_time)


def _skill_score(candidate, target_terms):
	if not target_terms:
		return 0.0

	candidate_terms = set(_tokenize(f"{candidate.ho_ten} {candidate.ky_nang} {candidate.vi_tri_mong_muon}"))
	if not candidate_terms:
		return 0.0

	return len(candidate_terms & target_terms) / len(target_terms)


def _availability_score(candidate, target_slots):
	if not target_slots:
		return 0.0

	candidate_slots = set(parse_candidate_slots(candidate))
	if not candidate_slots:
		return 0.0

	return len(candidate_slots & set(target_slots)) / len(set(target_slots))


def _location_score(candidate, target_location):
	if not target_location:
		return 0.0

	candidate_location = normalize_text(candidate.location)
	search_location = normalize_text(target_location)
	if not candidate_location or not search_location:
		return 0.0
	if candidate_location == search_location:
		return 1.0
	if candidate_location in search_location or search_location in candidate_location:
		return 0.7
	return 0.0


def _candidate_timestamp(candidate):
	updated_at = getattr(candidate, "updated_at", None)
	if updated_at is None:
		return 0.0
	return updated_at.timestamp()


def _build_slots_from_range(start_time, end_time):
	current_date = start_time.date()
	end_date = end_time.date()
	slots = set()

	while current_date <= end_date:
		weekday_label = WEEKDAY_LABELS[current_date.weekday()]
		if current_date == start_time.date() == end_date:
			if start_time.hour < 12:
				slots.add(f"{weekday_label}-AM")
			if end_time.hour >= 12:
				slots.add(f"{weekday_label}-PM")
		elif current_date == start_time.date():
			if start_time.hour < 12:
				slots.add(f"{weekday_label}-AM")
			slots.add(f"{weekday_label}-PM")
		elif current_date == end_date:
			slots.add(f"{weekday_label}-AM")
			if end_time.hour >= 12:
				slots.add(f"{weekday_label}-PM")
		else:
			slots.add(f"{weekday_label}-AM")
			slots.add(f"{weekday_label}-PM")

		current_date += timedelta(days=1)

	return slots


def _tokenize(value):
	normalized_value = normalize_text(value)
	if not normalized_value:
		return []

	tokens = [token for token in re.findall(r"[a-z0-9]+", normalized_value) if token not in TOKEN_STOPWORDS]
	return tokens
