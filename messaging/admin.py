"""
Admin configuration for Messaging app.
"""

from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin for Conversation model."""
    
    list_display = ['id', 'subject', 'participant_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['subject', 'participants__email']
    date_hierarchy = 'created_at'
    filter_horizontal = ['participants']
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin for Message model."""
    
    list_display = ['id', 'sender', 'conversation', 'is_read', 'created_at']
    list_filter = ['created_at', 'read_at']
    search_fields = ['sender__email', 'content']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'edited_at', 'read_at']
    
    def is_read(self, obj):
        return obj.is_read()
    is_read.boolean = True
    is_read.short_description = 'Read'
