from django.urls import path

from modules.chats.views import ChatConversationsAPIView, ChatMessagesAPIView

urlpatterns = [
	path("conversations/", ChatConversationsAPIView.as_view(), name="chat-conversations"),
	path("messages/", ChatMessagesAPIView.as_view(), name="chat-messages"),
]
