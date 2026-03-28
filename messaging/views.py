"""
Messaging views for user-to-user communication.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Max
from django.utils import timezone
from .models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def inbox(request):
    """Display user's conversations."""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        message_count=Count('messages'),
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')
    
    # Get unread counts for each conversation
    conversation_data = []
    for conv in conversations:
        last_message = conv.get_last_message()
        unread_count = conv.get_unread_count(request.user)
        
        conversation_data.append({
            'conversation': conv,
            'last_message': last_message,
            'unread_count': unread_count,
            'other_participants': conv.participants.exclude(id=request.user.id)
        })
    
    context = {
        'conversations': conversation_data,
        'page_title': 'Inbox'
    }
    
    return render(request, 'messaging/inbox.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """Display messages in a conversation."""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    # Mark messages as read
    conversation.mark_as_read(request.user)
    
    # Get messages
    message_list = conversation.messages.select_related('sender').all()
    
    # Get other participants
    other_participants = conversation.participants.exclude(id=request.user.id)
    
    context = {
        'conversation': conversation,
        'messages': message_list,
        'other_participants': other_participants,
        'page_title': 'Conversation'
    }
    
    return render(request, 'messaging/conversation_detail.html', context)


@login_required
def send_message(request):
    """Send a new message."""
    if request.method == 'POST':
        conversation_id = request.POST.get('conversation_id')
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content', '').strip()
        subject = request.POST.get('subject', '').strip()
        
        if not content:
            messages.error(request, 'Message content cannot be empty.')
            return redirect('messaging:inbox')
        
        # Get or create conversation
        if conversation_id:
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                participants=request.user
            )
        elif recipient_id:
            recipient = get_object_or_404(User, id=recipient_id)
            
            # Check if conversation already exists
            conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=recipient
            ).first()
            
            if not conversation:
                # Create new conversation
                conversation = Conversation.objects.create(subject=subject)
                conversation.participants.add(request.user, recipient)
        else:
            messages.error(request, 'Invalid request.')
            return redirect('messaging:inbox')
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )
        
        # Handle attachment if present
        if 'attachment' in request.FILES:
            message.attachments = request.FILES['attachment']
            message.save()
        
        messages.success(request, 'Message sent successfully.')
        return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    
    # GET request - show compose form
    recipient_id = request.GET.get('recipient')
    recipient = None
    if recipient_id:
        recipient = get_object_or_404(User, id=recipient_id)
    
    context = {
        'recipient': recipient,
        'page_title': 'Compose Message'
    }
    
    return render(request, 'messaging/compose.html', context)


@login_required
def mark_as_read(request, message_id):
    """Mark a message as read (AJAX endpoint)."""
    if request.method == 'POST':
        message = get_object_or_404(Message, id=message_id)
        
        # Verify user is a participant
        if not message.conversation.participants.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Don't mark own messages as read
        if message.sender != request.user:
            message.mark_as_read()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
def delete_conversation(request, conversation_id):
    """Delete a conversation (soft delete - remove user from participants)."""
    if request.method == 'POST':
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )
        
        # Remove user from participants
        conversation.participants.remove(request.user)
        
        # If no participants left, delete conversation
        if conversation.participants.count() == 0:
            conversation.delete()
        
        messages.success(request, 'Conversation deleted.')
        return redirect('messaging:inbox')
    
    return redirect('messaging:inbox')


@login_required
def search_users(request):
    """Search for users to message (AJAX endpoint)."""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    # Search users by email or name
    users = User.objects.filter(
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).exclude(id=request.user.id)[:10]
    
    user_data = [{
        'id': str(user.id),
        'email': user.email,
        'full_name': user.get_full_name() or user.email
    } for user in users]
    
    return JsonResponse({'users': user_data})
