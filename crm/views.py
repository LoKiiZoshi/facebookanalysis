from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import FacebookPage, FacebookPost, FacebookComment, FacebookMessage
from .facebook_api import FacebookGraphAPI
import json

def dashboard(request):
    """Main dashboard view displaying all Facebook data"""
    
    # Get all data from database
    pages = FacebookPage.objects.all()
    posts = FacebookPost.objects.all().order_by('-created_time')[:20]
    comments = FacebookComment.objects.all().order_by('-created_time')[:50]
    messages = FacebookMessage.objects.all().order_by('-created_time')[:50]
    
    # Calculate totals
    total_posts = FacebookPost.objects.count()
    total_likes = sum(post.likes_count for post in FacebookPost.objects.all())
    total_comments = FacebookComment.objects.count()
    total_shares = sum(post.shares_count for post in FacebookPost.objects.all())
    total_messages = FacebookMessage.objects.count()
    
    # Get recent activity
    recent_posts = FacebookPost.objects.order_by('-created_time')[:5]
    recent_comments = FacebookComment.objects.order_by('-created_time')[:10]
    recent_messages = FacebookMessage.objects.order_by('-created_time')[:10]
    
    context = {
        'pages': pages,
        'posts': posts,
        'comments': comments,
        'messages': messages,
        'total_posts': total_posts,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'total_messages': total_messages,
        'recent_posts': recent_posts,
        'recent_comments': recent_comments,
        'recent_messages': recent_messages,
    }
    
    return render(request, 'crm/dashboard.html', context)

def sync_facebook_data(request):
    """Sync data from Facebook Graph API"""
    
    try:
        api = FacebookGraphAPI()
        
        # Get pages
        pages_data = api.get_pages()
        if not pages_data or 'data' not in pages_data:
            messages.error(request, "Failed to fetch pages from Facebook API")
            return redirect('crm:dashboard')
        
        for page_data in pages_data['data']:
            page_id = page_data['id']
            
            # Get detailed page info
            page_info = api.get_page_info(page_id)
            if not page_info:
                continue
            
            # Create or update page
            page, created = FacebookPage.objects.get_or_create(
                page_id=page_id,
                defaults={
                    'name': page_info.get('name', ''),
                    'category': page_info.get('category', ''),
                    'followers_count': page_info.get('followers_count', 0) or page_info.get('fan_count', 0)
                }
            )
            
            if not created:
                page.name = page_info.get('name', page.name)
                page.category = page_info.get('category', page.category)
                page.followers_count = page_info.get('followers_count', 0) or page_info.get('fan_count', 0)
                page.save()
            
            # Get posts
            posts_data = api.get_page_posts(page_id)
            if posts_data and 'data' in posts_data:
                for post_data in posts_data['data']:
                    post_id = post_data['id']
                    
                    # Parse created time
                    created_time = datetime.fromisoformat(post_data['created_time'].replace('Z', '+00:00'))
                    
                    # Get engagement counts
                    likes_count = post_data.get('likes', {}).get('summary', {}).get('total_count', 0)
                    comments_count = post_data.get('comments', {}).get('summary', {}).get('total_count', 0)
                    shares_count = post_data.get('shares', {}).get('count', 0)
                    
                    # Create or update post
                    post, created = FacebookPost.objects.get_or_create(
                        post_id=post_id,
                        defaults={
                            'page': page,
                            'message': post_data.get('message', ''),
                            'created_time': created_time,
                            'likes_count': likes_count,
                            'comments_count': comments_count,
                            'shares_count': shares_count,
                        }
                    )
                    
                    if not created:
                        post.likes_count = likes_count
                        post.comments_count = comments_count
                        post.shares_count = shares_count
                        post.save()
                    
                    # Get comments for this post
                    comments_data = api.get_post_comments(post_id)
                    if comments_data and 'data' in comments_data:
                        for comment_data in comments_data['data']:
                            comment_id = comment_data['id']
                            comment_created_time = datetime.fromisoformat(comment_data['created_time'].replace('Z', '+00:00'))
                            
                            FacebookComment.objects.get_or_create(
                                comment_id=comment_id,
                                defaults={
                                    'post': post,
                                    'message': comment_data.get('message', ''),
                                    'from_name': comment_data.get('from', {}).get('name', 'Unknown'),
                                    'from_id': comment_data.get('from', {}).get('id', ''),
                                    'created_time': comment_created_time,
                                }
                            )
            
            # Get conversations/messages
            conversations_data = api.get_page_conversations(page_id)
            if conversations_data and 'data' in conversations_data:
                for conversation in conversations_data['data']:
                    conversation_id = conversation['id']
                    
                    # Get messages from this conversation
                    messages_data = api.get_conversation_messages(conversation_id)
                    if messages_data and 'data' in messages_data:
                        for message_data in messages_data['data']:
                            message_id = message_data['id']
                            
                            if 'created_time' in message_data:
                                message_created_time = datetime.fromisoformat(message_data['created_time'].replace('Z', '+00:00'))
                                
                                FacebookMessage.objects.get_or_create(
                                    message_id=message_id,
                                    defaults={
                                        'page': page,
                                        'message': message_data.get('message', ''),
                                        'from_name': message_data.get('from', {}).get('name', 'Unknown'),
                                        'from_id': message_data.get('from', {}).get('id', ''),
                                        'created_time': message_created_time,
                                    }
                                )
        
        messages.success(request, "Facebook data synced successfully!")
        
    except Exception as e:
        messages.error(request, f"Error syncing Facebook data: {str(e)}")
    
    return redirect('crm:dashboard')
