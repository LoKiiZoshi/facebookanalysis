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
    
    # Get permission info
    api = FacebookGraphAPI()
    permission_info = api.get_missing_permissions_info()
    
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
        'missing_permissions': permission_info['missing'],
        'granted_permissions': permission_info['granted'],
    }
    
    return render(request, 'crm/dashboard.html', context)

def sync_facebook_data(request):
    """Enhanced sync with improved comment user name extraction"""
    
    try:
        api = FacebookGraphAPI()
        
        print("=== STARTING ENHANCED FACEBOOK DATA SYNC ===")
        
        # Show permission status
        permission_info = api.get_missing_permissions_info()
        print(f"Missing permissions: {[p['permission'] for p in permission_info['missing']]}")
        print(f"Granted permissions: {[p['permission'] for p in permission_info['granted']]}")
        
        # Get pages
        pages_data = api.get_pages()
        if not pages_data or 'data' not in pages_data:
            messages.error(request, "Failed to fetch pages from Facebook API.")
            return redirect('crm:dashboard')
        
        for page_data in pages_data['data']:
            page_id = page_data['id']
            print(f"\n=== PROCESSING PAGE: {page_id} ===")
            
            # Get page info
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
            
            print(f"✅ Page saved: {page.name}")
            
            # Get posts with engagement
            posts_data = api.get_page_posts_with_all_engagement(page_id)
            
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
                    
                    # Extract engagement data
                    reactions_count = 0
                    comments_count = 0
                    shares_count = 0
                    likes_count = 0
                    
                    # Get reactions count
                    if 'reactions' in post_data and 'summary' in post_data['reactions']:
                        reactions_count = post_data['reactions']['summary'].get('total_count', 0)
                        print(f"Reactions found: {reactions_count}")
                    
                    # Get likes count (separate from reactions)
                    if 'likes' in post_data and 'summary' in post_data['likes']:
                        likes_count = post_data['likes']['summary'].get('total_count', 0)
                        print(f"Likes found: {likes_count}")
                    
                    # Use the higher of reactions or likes
                    final_likes_count = max(reactions_count, likes_count)
                    
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
                            'likes_count': final_likes_count,
                            'comments_count': comments_count,
                            'shares_count': shares_count,
                        }
                    )
                    
                    if not created:
                        post.message = message
                        post.likes_count = final_likes_count
                        post.comments_count = comments_count
                        post.shares_count = shares_count
                        post.save()
                    
                    print(f"✅ Post saved: Likes={final_likes_count}, Comments={comments_count}, Shares={shares_count}")
                    
                    # Get detailed comments with enhanced user info
                    if comments_count > 0:
                        print(f"Attempting to fetch {comments_count} comments with enhanced user details...")
                        comments_data = api.get_post_comments_with_enhanced_user_info(post_id, page_id)
                        
                        if comments_data and 'data' in comments_data:
                            print(f"✅ Successfully fetched {len(comments_data['data'])} comments with user details")
                            for comment_data in comments_data['data']:
                                comment_id = comment_data['id']
                                
                                # Parse comment time
                                comment_created_time_str = comment_data.get('created_time', '')
                                if comment_created_time_str:
                                    try:
                                        comment_created_time = datetime.fromisoformat(comment_created_time_str.replace('Z', '+00:00'))
                                    except:
                                        comment_created_time = datetime.now()
                                else:
                                    comment_created_time = datetime.now()
                                
                                # Enhanced user info extraction with Facebook API limitation handling
                                from_info = comment_data.get('from', {})
                                from_name = from_info.get('name', '')
                                from_id = from_info.get('id', '')
                                comment_message = comment_data.get('message', '')
                                
                                print(f"Raw comment data: {comment_data}")
                                print(f"From info: {from_info}")
                                print(f"Initial from_name: '{from_name}', from_id: '{from_id}'")
                                
                                # Handle Facebook API limitation where 'from' field is completely missing
                                if not from_info or (not from_name and not from_id):
                                    print(f"⚠️  Facebook API limitation: No user data available for comment {comment_id}")
                                    print("This happens when users have privacy settings that block app access")
                                    
                                    # Generate smart placeholder based on available data
                                    smart_name, extracted_id = api.generate_smart_placeholder_name(comment_id, comment_message)
                                    from_name = smart_name
                                    from_id = extracted_id
                                    
                                    print(f"Generated smart placeholder: {from_name} (ID: {from_id})")
                                
                                elif not from_name and from_id:
                                    # We have ID but no name - try to get user info
                                    print(f"Have user ID {from_id} but no name, trying to fetch user info...")
                                    user_info = api.get_user_profile_info(from_id, page_id)
                                    if user_info and user_info.get('name'):
                                        from_name = user_info['name']
                                        print(f"✅ Got user name from profile: {from_name}")
                                    else:
                                        from_name = f"User {from_id[:8]}..."
                                        print(f"Using ID-based placeholder: {from_name}")
                                
                                elif not from_name:
                                    # No name available at all
                                    smart_name, _ = api.generate_smart_placeholder_name(comment_id, comment_message)
                                    from_name = smart_name
                                    print(f"Using smart placeholder name: {from_name}")
                                
                                print(f"Final processing: {from_name} (ID: {from_id})")
                                
                                # Save comment with proper user info
                                comment_obj, comment_created = FacebookComment.objects.get_or_create(
                                    comment_id=comment_id,
                                    defaults={
                                        'post': post,
                                        'message': comment_message,
                                        'from_name': from_name,
                                        'from_id': from_id,
                                        'created_time': comment_created_time,
                                    }
                                )
                                
                                # Update existing comment if name was improved
                                if not comment_created:
                                    old_name = comment_obj.from_name
                                    if old_name in ['Anonymous User', 'Anonymous Commenter', 'Unknown User', ''] or 'Anonymous_' in old_name:
                                        comment_obj.from_name = from_name
                                        comment_obj.from_id = from_id
                                        comment_obj.save()
                                        print(f"✅ Updated existing comment: {old_name} → {from_name}")
                                
                                print(f"✅ Comment saved: {comment_id} by {from_name}")
                        else:
                            print(f"❌ Could not fetch comments with user details")
            
            # Get conversations and messages with full details
            print(f"\n--- Attempting to fetch messages for page {page_id} ---")
            conversations_data = api.get_page_conversations_with_details(page_id)
            
            if conversations_data and 'data' in conversations_data:
                print(f"✅ Found {len(conversations_data['data'])} conversations for page {page_id}")
                
                for conversation in conversations_data['data']:
                    conversation_id = conversation['id']
                    print(f"Processing conversation: {conversation_id}")
                    
                    # Get participants info
                    participants = conversation.get('participants', {}).get('data', [])
                    participant_names = [p.get('name', 'Unknown') for p in participants]
                    print(f"Conversation participants: {participant_names}")
                    
                    # Get messages from this conversation
                    messages_data = api.get_conversation_messages_with_full_details(conversation_id, page_id)
                    if messages_data and 'data' in messages_data:
                        print(f"✅ Found {len(messages_data['data'])} messages in conversation {conversation_id}")
                        
                        for message_data in messages_data['data']:
                            message_id = message_data['id']
                            
                            # Parse message time
                            if 'created_time' in message_data:
                                try:
                                    message_created_time = datetime.fromisoformat(message_data['created_time'].replace('Z', '+00:00'))
                                except:
                                    message_created_time = datetime.now()
                            else:
                                message_created_time = datetime.now()
                            
                            # Extract sender info
                            from_info = message_data.get('from', {})
                            from_name = from_info.get('name', 'Anonymous User')
                            from_id = from_info.get('id', '')
                            
                            # Get message content
                            message_content = message_data.get('message', '')
                            
                            # Handle attachments
                            attachments = message_data.get('attachments', {}).get('data', [])
                            if attachments and not message_content:
                                attachment_names = [att.get('name', 'Attachment') for att in attachments]
                                message_content = f"[Attachments: {', '.join(attachment_names)}]"
                            
                            print(f"Processing message from: {from_name} (ID: {from_id})")
                            print(f"Message content: {message_content[:50]}...")
                            
                            # Save message to database
                            FacebookMessage.objects.get_or_create(
                                message_id=message_id,
                                defaults={
                                    'page': page,
                                    'message': message_content,
                                    'from_name': from_name,
                                    'from_id': from_id,
                                    'created_time': message_created_time,
                                }
                            )
                            print(f"✅ Message saved: {message_id} from {from_name}")
                    else:
                        print(f"❌ Could not get messages for conversation {conversation_id}")
            else:
                print(f"❌ Could not access conversations for page {page_id}")
        
        print("\n=== SYNC COMPLETED ===")
        
        # Show results
        total_posts = FacebookPost.objects.count()
        total_comments = FacebookComment.objects.count()
        total_messages = FacebookMessage.objects.count()
        
        success_msg = f"Sync completed! Found: {total_posts} posts, {total_comments} comments, {total_messages} messages"
        messages.success(request, success_msg)
        
        if len(permission_info['missing']) > 0:
            missing_perms = ", ".join([p['permission'] for p in permission_info['missing']])
            messages.warning(request, f"Missing permissions for full access: {missing_perms}")
        
    except Exception as e:
        print(f"❌ General error in sync: {str(e)}")
        messages.error(request, f"Error syncing Facebook data: {str(e)}")
    
    return redirect('crm:dashboard')
