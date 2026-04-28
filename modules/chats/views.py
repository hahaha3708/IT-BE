from django.db.models import Q
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema

from modules.accounts.models import NguoiDung
from modules.applications.models import UngTuyen
from modules.chats.models import Chat
from modules.chats.serializers import (
	ChatMessageSerializer,
	ChatPaginatedConversationsSerializer,
	ChatPaginatedMessagesSerializer,
	ChatSendSerializer,
)


def _parse_pagination(query_params):
	try:
		page = int(query_params.get("page", 1))
	except (TypeError, ValueError):
		raise ValidationError({"page": "Page phai la so nguyen"})

	try:
		limit = int(query_params.get("limit", 20))
	except (TypeError, ValueError):
		raise ValidationError({"limit": "Limit phai la so nguyen"})

	if page < 1:
		raise ValidationError({"page": "Page phai lon hon hoac bang 1"})
	if limit < 1 or limit > 100:
		raise ValidationError({"limit": "Limit phai nam trong khoang 1-100"})

	return page, limit


def _paginate_items(items, page, limit):
	total = len(items)
	start_index = (page - 1) * limit
	end_index = start_index + limit
	return {
		"page": page,
		"limit": limit,
		"total": total,
		"results": items[start_index:end_index],
	}


def _resolve_display_name(user):
	if user.vai_tro == NguoiDung.VaiTro.UNG_VIEN:
		try:
			return user.ho_so_ung_vien.ho_ten
		except Exception:  # noqa: BLE001
			return user.email
	if user.vai_tro == NguoiDung.VaiTro.CONG_TY:
		try:
			return user.ho_so_cong_ty.ten_cong_ty
		except Exception:  # noqa: BLE001
			return user.email
	return user.email


def _validate_chat_pair(current_user, peer_user):
	if current_user.id == peer_user.id:
		raise PermissionDenied("Khong the nhan tin cho chinh minh")

	role_pair = {current_user.vai_tro, peer_user.vai_tro}
	if role_pair != {NguoiDung.VaiTro.UNG_VIEN, NguoiDung.VaiTro.CONG_TY}:
		raise PermissionDenied("Chi ho tro chat giua ung vien va nha tuyen dung")

	if current_user.vai_tro == NguoiDung.VaiTro.CONG_TY:
		recruiter_user_id = current_user.id
		candidate_user_id = peer_user.id
	else:
		recruiter_user_id = peer_user.id
		candidate_user_id = current_user.id

	has_relationship = UngTuyen.objects.filter(
		ung_vien_id=candidate_user_id,
		tin__cong_ty_id=recruiter_user_id,
	).exists()
	if not has_relationship:
		raise PermissionDenied("Hai tai khoan chua co quan he ung tuyen de bat dau chat")


class ChatConversationsAPIView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	@extend_schema(
		summary="Danh sach cuoc tro chuyen",
		description="Lay danh sach cuoc tro chuyen cua nguoi dung dang dang nhap, ho tro phan trang.",
		tags=["chats"],
		parameters=[
			OpenApiParameter(
				name="page",
				type=OpenApiTypes.INT,
				location=OpenApiParameter.QUERY,
				required=False,
				description="So trang bat dau tu 1",
			),
			OpenApiParameter(
				name="limit",
				type=OpenApiTypes.INT,
				location=OpenApiParameter.QUERY,
				required=False,
				description="So ban ghi moi trang (1-100)",
			),
		],
		responses={
			200: ChatPaginatedConversationsSerializer,
			400: OpenApiResponse(description="Tham so phan trang khong hop le"),
			401: OpenApiResponse(description="Chua xac thuc"),
		},
	)
	def get(self, request):
		page, limit = _parse_pagination(request.query_params)
		messages = (
			Chat.objects.filter(Q(nguoi_gui=request.user) | Q(nguoi_nhan=request.user))
			.select_related("nguoi_gui", "nguoi_nhan")
			.order_by("-thoi_gian_gui", "-tin_nhan_id")
		)

		conversation_map = {}
		for message in messages:
			peer = message.nguoi_nhan if message.nguoi_gui_id == request.user.id else message.nguoi_gui
			if peer.id in conversation_map:
				continue

			conversation_map[peer.id] = {
				"peer_user_id": peer.id,
				"peer_role": peer.vai_tro,
				"peer_display_name": _resolve_display_name(peer),
				"last_message": message.noi_dung_tin_nhan,
				"last_message_time": message.thoi_gian_gui,
			}

		ordered_conversations = list(conversation_map.values())
		pagination_payload = _paginate_items(ordered_conversations, page, limit)
		serializer = ChatPaginatedConversationsSerializer(pagination_payload)
		return Response(serializer.data)


class ChatMessagesAPIView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	@extend_schema(
		summary="Danh sach tin nhan voi mot nguoi dung",
		description="Lay lich su tin nhan giua nguoi dung hien tai va nguoi nhan, ho tro phan trang.",
		tags=["chats"],
		parameters=[
			OpenApiParameter(
				name="peer_user_id",
				type=OpenApiTypes.INT,
				location=OpenApiParameter.QUERY,
				required=True,
				description="ID nguoi dung doi thoai",
			),
			OpenApiParameter(
				name="page",
				type=OpenApiTypes.INT,
				location=OpenApiParameter.QUERY,
				required=False,
				description="So trang bat dau tu 1",
			),
			OpenApiParameter(
				name="limit",
				type=OpenApiTypes.INT,
				location=OpenApiParameter.QUERY,
				required=False,
				description="So ban ghi moi trang (1-100)",
			),
		],
		responses={
			200: ChatPaginatedMessagesSerializer,
			400: OpenApiResponse(description="Du lieu dau vao khong hop le"),
			401: OpenApiResponse(description="Chua xac thuc"),
			403: OpenApiResponse(description="Khong du quyen chat voi nguoi dung nay"),
		},
	)
	def get(self, request):
		page, limit = _parse_pagination(request.query_params)
		peer_user_id = request.query_params.get("peer_user_id")
		if not peer_user_id:
			raise ValidationError({"peer_user_id": "peer_user_id la bat buoc"})

		try:
			peer_user_id = int(peer_user_id)
		except (TypeError, ValueError):
			raise ValidationError({"peer_user_id": "peer_user_id phai la so nguyen"})

		peer_user = NguoiDung.objects.filter(pk=peer_user_id).first()
		if not peer_user:
			raise ValidationError({"peer_user_id": "Khong tim thay nguoi dung"})

		_validate_chat_pair(request.user, peer_user)

		queryset = (
			Chat.objects.filter(
				( Q(nguoi_gui=request.user) & Q(nguoi_nhan=peer_user) )
				| ( Q(nguoi_gui=peer_user) & Q(nguoi_nhan=request.user) )
			)
			.select_related("nguoi_gui", "nguoi_nhan")
			.order_by("thoi_gian_gui", "tin_nhan_id")
		)

		messages = list(queryset)
		pagination_payload = _paginate_items(messages, page, limit)
		response_serializer = ChatPaginatedMessagesSerializer(
			pagination_payload,
			context={"request": request},
		)
		return Response(response_serializer.data)

	@extend_schema(
		summary="Gui tin nhan",
		description="Gui mot tin nhan moi den nguoi dung khac khi co quan he ung tuyen hop le.",
		tags=["chats"],
		request=ChatSendSerializer,
		responses={
			201: ChatMessageSerializer,
			400: OpenApiResponse(description="Du lieu dau vao khong hop le"),
			401: OpenApiResponse(description="Chua xac thuc"),
			403: OpenApiResponse(description="Khong du quyen chat voi nguoi dung nay"),
		},
	)
	def post(self, request):
		serializer = ChatSendSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		nguoi_nhan_id = serializer.validated_data["nguoi_nhan_id"]
		peer_user = NguoiDung.objects.filter(pk=nguoi_nhan_id).first()
		if not peer_user:
			raise ValidationError({"nguoi_nhan_id": "Khong tim thay nguoi dung"})

		_validate_chat_pair(request.user, peer_user)

		message = Chat.objects.create(
			nguoi_gui=request.user,
			nguoi_nhan=peer_user,
			noi_dung_tin_nhan=serializer.validated_data["noi_dung_tin_nhan"],
		)

		message_serializer = ChatMessageSerializer(message, context={"request": request})
		return Response(message_serializer.data, status=201)
