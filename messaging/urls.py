"""
URL Configuration for Messaging app.
"""

from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('conversation/<uuid:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('send/', views.send_message, name='send_message'),
    path('mark-read/<uuid:message_id>/', views.mark_as_read, name='mark_as_read'),
    path('delete/<uuid:conversation_id>/', views.delete_conversation, name='delete_conversation'),
    path('search-users/', views.search_users, name='search_users'),
]
