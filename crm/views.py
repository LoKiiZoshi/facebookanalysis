from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import FacebookPage, FacebookPost, FacebookComment, FacebookMessag
import json



def dashboard(request):
    
    """Main dashboard view displaying all Facebook data"""
    
  
    
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
            