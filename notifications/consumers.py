"""
Django Channels WebSocket Consumer for Real-Time Notifications.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time user notifications."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get("user")
        
        # Reject unauthenticated connections
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Create unique channel group for this user
        self.group_name = f"notifications_{self.user.id}"
        
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'group_name'):
            # Leave group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
                
            elif message_type == 'mark_all_read':
                await self.mark_all_notifications_read()
                
            elif message_type == 'get_unread':
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': unread_count
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def notification_message(self, event):
        """
        Handle notification broadcast to user.
        Called when a notification is sent to the group.
        """
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    async def unread_count_update(self, event):
        """Handle unread count update broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': event['count']
        }))
    
    @database_sync_to_async
    def get_unread_count(self):
        """Get unread notification count for user."""
        from notifications.models import Notification
        return Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read."""
        from notifications.models import Notification
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all notifications as read for user."""
        from notifications.models import Notification
        Notification.mark_all_as_read(self.user)


# Helper function to send notification via WebSocket
async def send_notification_to_user(user_id, notification_data):
    """
    Send a notification to a specific user via WebSocket.
    
    Args:
        user_id: User ID to send notification to
        notification_data: Dictionary with notification details
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    group_name = f"notifications_{user_id}"
    
    await channel_layer.group_send(
        group_name,
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )


async def update_unread_count(user_id, count):
    """
    Update unread notification count for a user.
    
    Args:
        user_id: User ID
        count: New unread count
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    group_name = f"notifications_{user_id}"
    
    await channel_layer.group_send(
        group_name,
        {
            'type': 'unread_count_update',
            'count': count
        }
    )
