from rest_framework import serializers

from modules.chats.models import Chat


class ChatMessageSerializer(serializers.ModelSerializer):
	is_outgoing = serializers.SerializerMethodField()

	class Meta:
		model = Chat
		fields = (
			"tin_nhan_id",
			"nguoi_gui",
			"nguoi_nhan",
			"noi_dung_tin_nhan",
			"thoi_gian_gui",
			"is_outgoing",
		)

	def get_is_outgoing(self, instance):
		request = self.context.get("request")
		user = getattr(request, "user", None)
		if not user or not user.is_authenticated:
			return False
		return instance.nguoi_gui_id == user.id


class ChatSendSerializer(serializers.Serializer):
	nguoi_nhan_id = serializers.IntegerField(min_value=1)
	noi_dung_tin_nhan = serializers.CharField(max_length=5000)

	def validate_noi_dung_tin_nhan(self, value):
		normalized_value = value.strip()
		if not normalized_value:
			raise serializers.ValidationError("Noi dung tin nhan khong duoc de trong")
		return normalized_value


class ChatConversationSerializer(serializers.Serializer):
	peer_user_id = serializers.IntegerField()
	peer_role = serializers.CharField()
	peer_display_name = serializers.CharField()
	last_message = serializers.CharField(allow_blank=True)
	last_message_time = serializers.DateTimeField(allow_null=True)


class ChatPaginatedConversationsSerializer(serializers.Serializer):
	page = serializers.IntegerField()
	limit = serializers.IntegerField()
	total = serializers.IntegerField()
	results = ChatConversationSerializer(many=True)


class ChatPaginatedMessagesSerializer(serializers.Serializer):
	page = serializers.IntegerField()
	limit = serializers.IntegerField()
	total = serializers.IntegerField()
	results = ChatMessageSerializer(many=True)
