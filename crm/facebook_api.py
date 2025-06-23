import requests
from django.conf import settings
from datetime import datetime
import json

class FacebookGraphAPI:
    def __init__(self):
        self.access_token = settings.FACEBOOK_ACCESS_TOKEN
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def make_request(self, endpoint, params=None):
        """Make a request to Facebook Graph API"""
        if params is None:
            params = {}
        
        params['access_token'] = self.access_token
        
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {endpoint}: {e}")
            return None
    
    def get_pages(self):
        """Get all pages managed by the user"""
        return self.make_request("me/accounts")
    
    def get_page_info(self, page_id):
        """Get detailed information about a page"""
        fields = "id,name,category,followers_count,fan_count"
        return self.make_request(f"{page_id}", {"fields": fields})
    
    def get_page_posts(self, page_id, limit=25):
        """Get posts from a page"""
        fields = "id,message,created_time,likes.summary(true),comments.summary(true),shares"
        params = {
            "fields": fields,
            "limit": limit
        }
        return self.make_request(f"{page_id}/posts", params)
    
    def get_post_comments(self, post_id, limit=100):
        """Get comments for a specific post"""
        fields = "id,message,from,created_time"
        params = {
            "fields": fields,
            "limit": limit
        }
        return self.make_request(f"{post_id}/comments", params)
    
    def get_page_conversations(self, page_id, limit=25):
        """Get conversations/messages for a page"""
        fields = "id,snippet,updated_time,message_count,unread_count,participants"
        params = {
            "fields": fields,
            "limit": limit
        }
        return self.make_request(f"{page_id}/conversations", params)
    
    def get_conversation_messages(self, conversation_id, limit=50):
        """Get messages from a specific conversation"""
        fields = "id,message,from,created_time"
        params = {
            "fields": fields,
            "limit": limit
        }
        return self.make_request(f"{conversation_id}/messages", params)
    
    def get_page_insights(self, page_id):
        """Get page insights/analytics"""
        metrics = "page_fans,page_impressions,page_engaged_users"
        params = {
            "metric": metrics,
            "period": "day"
        }
        return self.make_request(f"{page_id}/insights", params)
