import requests
from django.conf import settings
from datetime import datetime
import json

class FacebookGraphAPI:
    def __init__(self):
        self.user_access_token = settings.FACEBOOK_ACCESS_TOKEN
        self.base_url = "https://graph.facebook.com/v19.0"
        self.page_tokens = {}  # Store page access tokens
    
    def make_request(self, endpoint, params=None, access_token=None):
        """Make a request to Facebook Graph API with better error handling"""
        if params is None:
            params = {}
        
        # Use provided access token or default user token
        token = access_token or self.user_access_token
        params['access_token'] = token
        
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            
            if response.status_code == 400:
                error_data = response.json()
                print(f"API Error for {endpoint}: {error_data}")
                return None
            elif response.status_code == 403:
                print(f"Permission denied for {endpoint}. Check your access token permissions.")
                return None
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {endpoint}: {e}")
            return None
    
    def get_page_access_token(self, page_id):
        """Get page access token for a specific page"""
        if page_id in self.page_tokens:
            return self.page_tokens[page_id]
        
        # Get all pages with their access tokens
        pages_data = self.make_request("me/accounts")
        if pages_data and 'data' in pages_data:
            for page in pages_data['data']:
                if page['id'] == page_id:
                    page_token = page.get('access_token')
                    if page_token:
                        self.page_tokens[page_id] = page_token
                        print(f"Got page access token for {page_id}")
                        return page_token
        
        print(f"Could not get page access token for {page_id}")
        return None
    
    def get_pages(self):
        """Get all pages managed by the user"""
        return self.make_request("me/accounts")
    
    def get_page_info(self, page_id):
        """Get detailed information about a page"""
        fields = "id,name,category,fan_count,followers_count"
        page_token = self.get_page_access_token(page_id)
        return self.make_request(f"{page_id}", {"fields": fields}, page_token)
    
    def get_page_posts_with_engagement(self, page_id, limit=25):
        """Get posts from a page with engagement data included"""
        # Include engagement fields directly in the posts request
        fields = "id,message,created_time,story,reactions.summary(total_count),comments.summary(total_count),shares"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
        
        print(f"Fetching posts with engagement for page {page_id}")
        return self.make_request(f"{page_id}/posts", params, page_token)
    
    def get_page_feed_with_engagement(self, page_id, limit=25):
        """Alternative method to get page feed with engagement data"""
        fields = "id,message,created_time,story,type,reactions.summary(total_count),comments.summary(total_count),shares"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
            
        print(f"Fetching feed with engagement for page {page_id}")
        return self.make_request(f"{page_id}/feed", params, page_token)
    
    def get_post_reactions_detailed(self, post_id, page_id):
        """Get detailed reactions for a post"""
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
        
        # Get all reactions with types
        reactions_data = self.make_request(f"{post_id}/reactions", {
            "summary": "total_count"
        }, page_token)
        
        return reactions_data
    
    def get_post_comments_with_details(self, post_id, page_id, limit=100):
        """Get comments for a specific post with full user details"""
        fields = "id,message,from{id,name},created_time,like_count,comment_count"
        params = {
            "fields": fields,
            "limit": limit,
            "order": "chronological"
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
        
        print(f"Fetching comments for post {post_id}")
        return self.make_request(f"{post_id}/comments", params, page_token)
    
    def get_page_conversations_detailed(self, page_id, limit=25):
        """Get conversations/messages for a page with detailed info"""
        fields = "id,snippet,updated_time,message_count,unread_count,participants,can_reply"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
        
        print(f"Fetching conversations for page {page_id}")
        return self.make_request(f"{page_id}/conversations", params, page_token)
    
    def get_conversation_messages_detailed(self, conversation_id, page_id, limit=50):
        """Get messages from a specific conversation with full details"""
        fields = "id,message,from{id,name},created_time,attachments"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
        
        print(f"Fetching messages for conversation {conversation_id}")
        return self.make_request(f"{conversation_id}/messages", params, page_token)
    
    def get_page_insights(self, page_id):
        """Get page insights for engagement metrics"""
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
        
        metrics = [
            "page_post_engagements",
            "page_posts_impressions", 
            "page_fan_adds",
            "page_fan_removes"
        ]
        
        params = {
            "metric": ",".join(metrics),
            "period": "day",
            "since": "2024-01-01"
        }
        
        return self.make_request(f"{page_id}/insights", params, page_token)
    
    def debug_token(self):
        """Debug the access token to see what permissions it has"""
        params = {
            'input_token': self.user_access_token,
            'access_token': f"{settings.FACEBOOK_APP_ID}|{settings.FACEBOOK_APP_SECRET}"
        }
        return self.make_request("debug_token", params)
    
    def get_my_permissions(self):
        """Get permissions for the current access token"""
        return self.make_request("me/permissions")
    
    def test_page_permissions(self, page_id):
        """Test what permissions we have for a specific page"""
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return {"error": "No page token available"}
        
        tests = {}
        
        # Test posts access
        posts_test = self.make_request(f"{page_id}/posts", {"limit": 1}, page_token)
        tests['posts_access'] = posts_test is not None
        
        # Test conversations access  
        conv_test = self.make_request(f"{page_id}/conversations", {"limit": 1}, page_token)
        tests['conversations_access'] = conv_test is not None
        
        # Test insights access
        insights_test = self.make_request(f"{page_id}/insights", {"metric": "page_fans", "period": "day"}, page_token)
        tests['insights_access'] = insights_test is not None
        
        return tests
