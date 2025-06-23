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
    """Sync data from Facebook Graph API with proper page access tokens"""
    
    try:
        api = FacebookGraphAPI()
        
        # Debug token first
        print("Debugging access token...")
        token_debug = api.debug_token()
        if token_debug:
            print(f"Token debug info: {token_debug}")
        
        # Check permissions
        permissions = api.get_my_permissions()
        if permissions:
            print(f"Available permissions: {permissions}")
        
        # Get pages
        pages_data = api.get_pages()
        if not pages_data or 'data' not in pages_data:
            messages.error(request, "Failed to fetch pages from Facebook API. Check your access token permissions.")
            return redirect('crm:dashboard')
        
        for page_data in pages_data['data']:
            page_id = page_data['id']
            print(f"Processing page: {page_id}")
            
            # Get page access token
            page_token = api.get_page_access_token(page_id)
            if not page_token:
                print(f"Could not get page access token for {page_id}")
                continue
            
            # Get detailed page info
            page_info = api.get_page_info(page_id)
            if not page_info:
                print(f"Could not get info for page {page_id}")
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
            
            print(f"Page saved: {page.name}")
            
            # Try to get posts using page token
            posts_data = api.get_page_posts_simple(page_id)
            if not posts_data or 'data' not in posts_data:
                print(f"Trying alternative feed method for page {page_id}")
                posts_data = api.get_page_feed(page_id)
            
            if posts_data and 'data' in posts_data:
                print(f"Found {len(posts_data['data'])} posts for page {page_id}")
                
                for post_data in posts_data['data']:
                    post_id = post_data['id']
                    
                    # Parse created time
                    created_time_str = post_data.get('created_time', '')
                    if created_time_str:
                        try:
                            created_time = datetime.fromisoformat(created_time_str.replace('Z', '+00:00'))
                        except:
                            created_time = datetime.now()
                    else:
                        created_time = datetime.now()
                    
                    # Get message content
                    message = post_data.get('message', '') or post_data.get('story', '')
                    
                    # Create or update post
                    post, created = FacebookPost.objects.get_or_create(
                        post_id=post_id,
                        defaults={
                            'page': page,
                            'message': message,
                            'created_time': created_time,
                            'likes_count': 0,
                            'comments_count': 0,
                            'shares_count': 0,
                        }
                    )
                    
                    print(f"Post saved: {post_id}")
                    
                    # Try to get engagement data with page token
                    try:
                        engagement = api.get_post_engagement(post_id, page_id)
                        post.likes_count = engagement['likes_count']
                        post.comments_count = engagement['comments_count']
                        post.shares_count = engagement['shares_count']
                        post.save()
                        print(f"Engagement updated for post {post_id}: {engagement}")
                    except Exception as e:
                        print(f"Could not get engagement for post {post_id}: {e}")
                    
                    # Try to get comments with page token
                    try:
                        comments_data = api.get_post_comments_detailed(post_id, page_id)
                        if comments_data and 'data' in comments_data:
                            print(f"Found {len(comments_data['data'])} comments for post {post_id}")
                            for comment_data in comments_data['data']:
                                comment_id = comment_data['id']
                                comment_created_time_str = comment_data.get('created_time', '')
                                
                                if comment_created_time_str:
                                    try:
                                        comment_created_time = datetime.fromisoformat(comment_created_time_str.replace('Z', '+00:00'))
                                    except:
                                        comment_created_time = datetime.now()
                                else:
                                    comment_created_time = datetime.now()
                                
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
                                print(f"Comment saved: {comment_id} by {comment_data.get('from', {}).get('name', 'Unknown')}")
                    except Exception as e:
                        print(f"Could not get comments for post {post_id}: {e}")
            else:
                print(f"No posts found for page {page_id}")
            
            # Try to get messages/conversations with page token
            try:
                conversations_data = api.get_page_conversations(page_id)
                if conversations_data and 'data' in conversations_data:
                    print(f"Found {len(conversations_data['data'])} conversations for page {page_id}")
                    for conversation in conversations_data['data']:
                        conversation_id = conversation['id']
                        
                        # Get messages from this conversation
                        messages_data = api.get_conversation_messages(conversation_id, page_id)
                        if messages_data and 'data' in messages_data:
                            print(f"Found {len(messages_data['data'])} messages in conversation {conversation_id}")
                            for message_data in messages_data['data']:
                                message_id = message_data['id']
                                
                                if 'created_time' in message_data:
                                    try:
                                        message_created_time = datetime.fromisoformat(message_data['created_time'].replace('Z', '+00:00'))
                                    except:
                                        message_created_time = datetime.now()
                                    
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
                                    print(f"Message saved: {message_id} from {message_data.get('from', {}).get('name', 'Unknown')}")
                else:
                    print(f"No conversations found for page {page_id}")
            except Exception as e:
                print(f"Could not get conversations for page {page_id}: {e}")
        
        messages.success(request, "Facebook data sync completed! Check the console for detailed logs.")
        
    except Exception as e:
        print(f"General error in sync: {str(e)}")
        messages.error(request, f"Error syncing Facebook data: {str(e)}")
    
    return redirect('crm:dashboard')
