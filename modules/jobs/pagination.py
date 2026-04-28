from rest_framework.exceptions import ValidationError


class JobPagination:
	default_page = 1
	default_limit = 20
	max_limit = 100
	page_query_param = "page"
	limit_query_param = "limit"

	def parse(self, query_params):
		page = self._parse_int(query_params.get("page"), "page", minimum=1, default=self.default_page)
		limit = self._parse_int(query_params.get("limit"), "limit", minimum=1, maximum=self.max_limit, default=self.default_limit)
		return page, limit

	def paginate_queryset(self, queryset, query_params):
		page, limit = self.parse(query_params)
		total = queryset.count()
		start = (page - 1) * limit
		end = start + limit
		return {
			"page": page,
			"limit": limit,
			"total": total,
			"results": queryset[start:end],
		}

	def get_schema_operation_parameters(self, view):
		return [
			{
				"name": self.page_query_param,
				"required": False,
				"in": "query",
				"description": "1-based page number.",
				"schema": {"type": "integer"},
			},
			{
				"name": self.limit_query_param,
				"required": False,
				"in": "query",
				"description": "Page size up to 100.",
				"schema": {"type": "integer"},
			},
		]

	def get_paginated_response_schema(self, schema):
		return {
			"type": "object",
			"properties": {
				"page": {"type": "integer"},
				"limit": {"type": "integer"},
				"total": {"type": "integer"},
				"results": {
					"type": "array",
					"items": schema,
				},
			},
			"required": ["page", "limit", "total", "results"],
		}

	@staticmethod
	def _parse_int(value, field_name, minimum=None, maximum=None, default=None):
		if value in (None, ""):
			return default

		try:
			parsed_value = int(str(value).strip())
		except (TypeError, ValueError) as exc:
			raise ValidationError({field_name: "Must be a valid integer"}) from exc

		if minimum is not None and parsed_value < minimum:
			raise ValidationError({field_name: f"Must be greater than or equal to {minimum}"})
		if maximum is not None and parsed_value > maximum:
			raise ValidationError({field_name: f"Must be less than or equal to {maximum}"})

		return parsed_value
