"""
Messaging models for user-to-user communication.
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Conversation(models.Model):
    """Represents a conversation between users."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    subject = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']
    
    def __str__(self):
        participant_names = ', '.join([u.get_full_name() or u.email for u in self.participants.all()[:3]])
        return f"Conversation: {participant_names}"
    
    def get_last_message(self):
        """Get the last message in this conversation."""
        return self.messages.order_by('-created_at').first()
    
    def get_unread_count(self, user):
        """Get unread message count for a specific user."""
        return self.messages.filter(
            read_by__isnull=True
        ).exclude(sender=user).count()
    
    def mark_as_read(self, user):
        """Mark all messages in conversation as read for a user."""
        messages = self.messages.exclude(sender=user).filter(
            read_at__isnull=True
        )
        now = timezone.now()
        for message in messages:
            message.read_at = now
            message.save(update_fields=['read_at'])


class Message(models.Model):
    """Represents a message in a conversation."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    attachments = models.FileField(
        upload_to='message_attachments/%Y/%m/',
        blank=True,
        null=True
    )
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.email} at {self.created_at}"
    
    def mark_as_read(self):
        """Mark message as read."""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])
    
    def is_read(self):
        """Check if message has been read."""
        return self.read_at is not None
