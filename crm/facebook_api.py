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
    
    def get_page_posts_simple(self, page_id, limit=25):
        """Get posts from a page with page access token"""
        fields = "id,message,created_time,story"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
        
        return self.make_request(f"{page_id}/posts", params, page_token)
    
    def get_page_feed(self, page_id, limit=25):
        """Alternative method to get page feed with page access token"""
        fields = "id,message,created_time,story,type"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
            
        return self.make_request(f"{page_id}/feed", params, page_token)
    
    def get_post_engagement(self, post_id, page_id):
        """Get engagement data for a specific post using page token"""
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return {'likes_count': 0, 'comments_count': 0, 'shares_count': 0}
        
        # Try to get likes
        likes_data = self.make_request(f"{post_id}/likes", {"summary": "true", "limit": 0}, page_token)
        likes_count = 0
        if likes_data and 'summary' in likes_data:
            likes_count = likes_data['summary'].get('total_count', 0)
        
        # Try to get comments
        comments_data = self.make_request(f"{post_id}/comments", {"summary": "true", "limit": 0}, page_token)
        comments_count = 0
        if comments_data and 'summary' in comments_data:
            comments_count = comments_data['summary'].get('total_count', 0)
        
        # Try to get shares (this might not be available)
        shares_count = 0
        
        return {
            'likes_count': likes_count,
            'comments_count': comments_count,
            'shares_count': shares_count
        }
    
    def get_post_comments_detailed(self, post_id, page_id, limit=100):
        """Get comments for a specific post with user details using page token"""
        fields = "id,message,from,created_time"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
            
        return self.make_request(f"{post_id}/comments", params, page_token)
    
    def get_page_conversations(self, page_id, limit=25):
        """Get conversations/messages for a page using page token"""
        fields = "id,snippet,updated_time,message_count,unread_count"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
            
        return self.make_request(f"{page_id}/conversations", params, page_token)
    
    def get_conversation_messages(self, conversation_id, page_id, limit=50):
        """Get messages from a specific conversation using page token"""
        fields = "id,message,from,created_time"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
            
        return self.make_request(f"{conversation_id}/messages", params, page_token)
    
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
