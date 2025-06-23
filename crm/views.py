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
    """Enhanced sync with better engagement and message fetching"""
    
    try:
        api = FacebookGraphAPI()
        
        # Debug token first
        print("=== STARTING FACEBOOK DATA SYNC ===")
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
            messages.error(request, "Failed to fetch pages from Facebook API.")
            return redirect('crm:dashboard')
        
        for page_data in pages_data['data']:
            page_id = page_data['id']
            print(f"\n=== PROCESSING PAGE: {page_id} ===")
            
            # Test page permissions
            page_permissions = api.test_page_permissions(page_id)
            print(f"Page permissions test: {page_permissions}")
            
            # Get page access token
            page_token = api.get_page_access_token(page_id)
            if not page_token:
                print(f"❌ Could not get page access token for {page_id}")
                continue
            
            # Get detailed page info
            page_info = api.get_page_info(page_id)
            if not page_info:
                print(f"❌ Could not get info for page {page_id}")
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
            
            print(f"✅ Page saved: {page.name}")
            
            # Get posts with engagement data
            posts_data = api.get_page_posts_with_engagement(page_id)
            if not posts_data or 'data' not in posts_data:
                print(f"Trying alternative feed method for page {page_id}")
                posts_data = api.get_page_feed_with_engagement(page_id)
            
            if posts_data and 'data' in posts_data:
                print(f"✅ Found {len(posts_data['data'])} posts for page {page_id}")
                
                for post_data in posts_data['data']:
                    post_id = post_data['id']
                    print(f"\n--- Processing post: {post_id} ---")
                    
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
                    
                    # Extract engagement data from the post response
                    reactions_count = 0
                    comments_count = 0
                    shares_count = 0
                    
                    # Get reactions count
                    if 'reactions' in post_data and 'summary' in post_data['reactions']:
                        reactions_count = post_data['reactions']['summary'].get('total_count', 0)
                        print(f"Reactions found: {reactions_count}")
                    
                    # Get comments count
                    if 'comments' in post_data and 'summary' in post_data['comments']:
                        comments_count = post_data['comments']['summary'].get('total_count', 0)
                        print(f"Comments found: {comments_count}")
                    
                    # Get shares count
                    if 'shares' in post_data:
                        shares_count = post_data['shares'].get('count', 0)
                        print(f"Shares found: {shares_count}")
                    
                    # Create or update post
                    post, created = FacebookPost.objects.get_or_create(
                        post_id=post_id,
                        defaults={
                            'page': page,
                            'message': message,
                            'created_time': created_time,
                            'likes_count': reactions_count,  # Using reactions as likes
                            'comments_count': comments_count,
                            'shares_count': shares_count,
                        }
                    )
                    
                    if not created:
                        post.message = message
                        post.likes_count = reactions_count
                        post.comments_count = comments_count
                        post.shares_count = shares_count
                        post.save()
                    
                    print(f"✅ Post saved with engagement: Reactions={reactions_count}, Comments={comments_count}, Shares={shares_count}")
                    
                    # Get detailed comments if there are any
                    if comments_count > 0:
                        try:
                            comments_data = api.get_post_comments_with_details(post_id, page_id)
                            if comments_data and 'data' in comments_data:
                                print(f"✅ Found {len(comments_data['data'])} detailed comments for post {post_id}")
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
                                    
                                    from_info = comment_data.get('from', {})
                                    from_name = from_info.get('name', 'Unknown User')
                                    from_id = from_info.get('id', '')
                                    
                                    FacebookComment.objects.get_or_create(
                                        comment_id=comment_id,
                                        defaults={
                                            'post': post,
                                            'message': comment_data.get('message', ''),
                                            'from_name': from_name,
                                            'from_id': from_id,
                                            'created_time': comment_created_time,
                                        }
                                    )
                                    print(f"✅ Comment saved: {comment_id} by {from_name}")
                        except Exception as e:
                            print(f"❌ Could not get comments for post {post_id}: {e}")
            else:
                print(f"❌ No posts found for page {page_id}")
            
            # Get conversations and messages
            try:
                print(f"\n--- Fetching conversations for page {page_id} ---")
                conversations_data = api.get_page_conversations_detailed(page_id)
                if conversations_data and 'data' in conversations_data:
                    print(f"✅ Found {len(conversations_data['data'])} conversations for page {page_id}")
                    for conversation in conversations_data['data']:
                        conversation_id = conversation['id']
                        print(f"Processing conversation: {conversation_id}")
                        
                        # Get messages from this conversation
                        messages_data = api.get_conversation_messages_detailed(conversation_id, page_id)
                        if messages_data and 'data' in messages_data:
                            print(f"✅ Found {len(messages_data['data'])} messages in conversation {conversation_id}")
                            for message_data in messages_data['data']:
                                message_id = message_data['id']
                                
                                if 'created_time' in message_data:
                                    try:
                                        message_created_time = datetime.fromisoformat(message_data['created_time'].replace('Z', '+00:00'))
                                    except:
                                        message_created_time = datetime.now()
                                    
                                    from_info = message_data.get('from', {})
                                    from_name = from_info.get('name', 'Unknown User')
                                    from_id = from_info.get('id', '')
                                    
                                    FacebookMessage.objects.get_or_create(
                                        message_id=message_id,
                                        defaults={
                                            'page': page,
                                            'message': message_data.get('message', ''),
                                            'from_name': from_name,
                                            'from_id': from_id,
                                            'created_time': message_created_time,
                                        }
                                    )
                                    print(f"✅ Message saved: {message_id} from {from_name}")
                else:
                    print(f"❌ No conversations found for page {page_id}")
            except Exception as e:
                print(f"❌ Could not get conversations for page {page_id}: {e}")
        
        print("\n=== SYNC COMPLETED ===")
        messages.success(request, "Facebook data sync completed! Check the console for detailed logs.")
        
    except Exception as e:
        print(f"❌ General error in sync: {str(e)}")
        messages.error(request, f"Error syncing Facebook data: {str(e)}")
    
    return redirect('crm:dashboard')
