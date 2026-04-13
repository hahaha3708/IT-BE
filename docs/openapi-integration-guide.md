# OpenAPI Integration Guide

## Muc tieu
- Dung Swagger/ReDoc de test BE endpoint nhanh hon.
- Giu request examples va error responses dong bo voi contract trong `docs/contract/`.
- An endpoint noi bo/test khoi production schema.

## Route tai lieu
- Schema JSON: `/api/schema/`
- Swagger UI: `/api/docs/swagger/`
- ReDoc: `/api/docs/redoc/`

## Cach auth trong Swagger
1. Goi `POST /api/auth/token/` de lay access token.
2. Mo Swagger UI, bam `Authorize`.
3. Nhap `Bearer <access_token>`.

## Quy uoc viet doc endpoint
- Moi endpoint co `summary`, `description`, `tags`.
- Endpoint co request body phai co request example day du.
- Endpoint co query params phai khai bao ro kieu du lieu, gia tri mac dinh, enum neu co.
- Endpoint protected phai the hien ro JWT hoac role constraint trong description.
- Endpoint loi phai co it nhat mot error example cho 400/401/403/404 neu ap dung.

## Mau request can co
- Path params: `job_id`, `candidate_id`, `id`.
- Query params: `page`, `limit`, `sort`, `q`, `location`, `salary_min`, `salary_max`, `availability_slots`.
- Body params: day du theo serializer, bao gom field bat buoc va field tuy chon.
- Header params: `Authorization`, `X-Test-Token-Secret` neu dung test token endpoint.

## Luu y
- `/api/auth/test-token/` chi phuc vu local/dev va se khong xuat hien trong schema production.
- Schema phai duoc kiem tra lai sau moi lan them endpoint moi hoac doi serializer.