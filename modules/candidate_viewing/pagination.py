from rest_framework.exceptions import ValidationError


class CandidatePagination:
	default_page = 1
	default_limit = 20
	max_limit = 100

	def parse(self, query_params):
		page = self._parse_int(query_params.get("page"), "page", minimum=1, default=self.default_page)
		limit = self._parse_int(query_params.get("limit"), "limit", minimum=1, maximum=self.max_limit, default=self.default_limit)
		return page, limit

	def paginate(self, items, query_params):
		page, limit = self.parse(query_params)
		total = len(items)
		start = (page - 1) * limit
		end = start + limit
		return {
			"page": page,
			"limit": limit,
			"total": total,
			"results": items[start:end],
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
