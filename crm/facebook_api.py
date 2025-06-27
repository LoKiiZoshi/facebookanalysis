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
    
    def get_page_posts_with_all_engagement(self, page_id, limit=25):
        """Get posts with maximum available engagement data"""
        fields = "id,message,created_time,story,reactions.summary(total_count),comments.summary(total_count),shares,likes.summary(total_count)"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
        
        print(f"Fetching posts with maximum engagement data for page {page_id}")
        result = self.make_request(f"{page_id}/posts", params, page_token)
        
        # If that fails, try with basic fields
        if not result:
            print("Trying with basic engagement fields...")
            fields = "id,message,created_time,story,reactions.summary(total_count)"
            params = {"fields": fields, "limit": limit}
            result = self.make_request(f"{page_id}/posts", params, page_token)
        
        return result
    
    def get_post_comments_with_enhanced_user_info(self, post_id, page_id, limit=100):
        """Get comments with enhanced user information using multiple methods"""
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
    
        print(f"Fetching comments with enhanced user info for post {post_id}")
    
        # Method 1: Try to get comments with reactions to extract user IDs
        fields = "id,message,from{id,name,picture.type(large)},created_time,like_count,comment_count,parent,reactions{id,name,type}"
        params = {
            "fields": fields,
            "limit": limit,
            "order": "chronological"
        }
    
        comments_data = self.make_request(f"{post_id}/comments", params, page_token)
    
        if comments_data and 'data' in comments_data:
            print(f"Method 1 successful: Found {len(comments_data['data'])} comments")
            return comments_data
    
        # Method 2: Try with basic fields but include reactions
        print("Method 1 failed, trying Method 2 with reactions...")
        fields = "id,message,from,created_time,reactions.limit(1){id,name}"
        params = {
            "fields": fields,
            "limit": limit
        }
    
        comments_data = self.make_request(f"{post_id}/comments", params, page_token)
    
        if comments_data and 'data' in comments_data:
            print(f"Method 2 successful: Found {len(comments_data['data'])} comments")
            return comments_data
    
        # Method 3: Try to get comment IDs and fetch individual comments
        print("Method 2 failed, trying Method 3 with individual comment fetching...")
        params = {"limit": limit}
    
        comments_data = self.make_request(f"{post_id}/comments", params, page_token)
    
        if comments_data and 'data' in comments_data:
            print(f"Method 3 successful: Found {len(comments_data['data'])} comments")
        
            # Try to enhance each comment individually
            for comment in comments_data['data']:
                if not comment.get('from') or not comment.get('from', {}).get('name'):
                    comment_id = comment['id']
                    print(f"Trying to get individual comment data for {comment_id}")
                
                    # Try to get individual comment with user info
                    individual_comment = self.make_request(f"{comment_id}", {
                        "fields": "id,message,from{id,name},created_time"
                    }, page_token)
                
                    if individual_comment and individual_comment.get('from'):
                        comment['from'] = individual_comment['from']
                        print(f"✅ Enhanced comment {comment_id} with user info")
        
            return comments_data
    
        # Method 4: Try with user access token
        print("Method 3 failed, trying Method 4 with user token...")
        fields = "id,message,from{id,name},created_time"
        params = {
            "fields": fields,
            "limit": limit
        }
    
        comments_data = self.make_request(f"{post_id}/comments", params, self.user_access_token)
    
        if comments_data and 'data' in comments_data:
            print(f"Method 4 successful: Found {len(comments_data['data'])} comments")
            return comments_data
    
        print("All methods failed to get comments")
        return None

    
    def get_user_profile_info(self, user_id, page_id):
        """Get detailed user profile information"""
        page_token = self.get_page_access_token(page_id)
        
        # Try multiple methods to get user info
        methods = [
            {"token": page_token, "name": "page token"},
            {"token": self.user_access_token, "name": "user token"}
        ]
        
        for method in methods:
            if not method["token"]:
                continue
                
            print(f"Trying to get user {user_id} info with {method['name']}")
            
            # Try different field combinations
            field_combinations = [
                "id,name,picture.type(large)",
                "id,name,picture",
                "id,name",
                "name"
            ]
            
            for fields in field_combinations:
                try:
                    user_info = self.make_request(f"{user_id}", {"fields": fields}, method["token"])
                    if user_info and user_info.get('name'):
                        print(f"✅ Got user info for {user_id}: {user_info.get('name')}")
                        return user_info
                except:
                    continue
        
        print(f"❌ Could not get user info for {user_id}")
        return None
    
    def get_page_conversations_with_details(self, page_id, limit=25):
        """Get conversations with detailed participant information"""
        fields = "id,snippet,updated_time,message_count,unread_count,participants{id,name,email},can_reply"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
        
        print(f"Fetching detailed conversations for page {page_id}")
        return self.make_request(f"{page_id}/conversations", params, page_token)
    
    def get_conversation_messages_with_full_details(self, conversation_id, page_id, limit=50):
        """Get messages with complete sender information"""
        fields = "id,message,from{id,name,email,picture},to{data{id,name}},created_time,attachments{name,mime_type,file_url}"
        params = {
            "fields": fields,
            "limit": limit
        }
        page_token = self.get_page_access_token(page_id)
        if not page_token:
            return None
        
        print(f"Fetching detailed messages for conversation {conversation_id}")
        return self.make_request(f"{conversation_id}/messages", params, page_token)
    
    def get_missing_permissions_info(self):
        """Get information about what permissions are missing"""
        current_permissions = self.get_my_permissions()
        
        required_permissions = {
            'pages_read_engagement': 'To read comments, likes, and reactions on posts',
            'pages_messaging': 'To read and send messages through the page',
            'pages_read_user_content': 'To read user-generated content on the page',
            'read_insights': 'To access page insights and analytics'
        }
        
        missing = []
        granted = []
        
        if current_permissions and 'data' in current_permissions:
            granted_perms = [p['permission'] for p in current_permissions['data'] if p['status'] == 'granted']
            
            for perm, description in required_permissions.items():
                if perm not in granted_perms:
                    missing.append({'permission': perm, 'description': description})
                else:
                    granted.append({'permission': perm, 'description': description})
        
        return {
            'missing': missing,
            'granted': granted,
            'current_permissions': current_permissions
        }
    
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

    def extract_user_from_comment_id(self, comment_id):
        """Try to extract user information from comment ID pattern"""
        try:
            # Facebook comment IDs sometimes contain user information
            # Format is often: POST_ID_USER_TIMESTAMP or similar
            parts = comment_id.split('_')
            if len(parts) >= 2:
                potential_user_id = parts[1]
                # Check if this looks like a user ID (numeric and reasonable length)
                if potential_user_id.isdigit() and 10 <= len(potential_user_id) <= 20:
                    return potential_user_id
        except:
            pass
        return None

    def generate_smart_placeholder_name(self, comment_id, comment_message):
        """Generate a smarter placeholder name based on available data"""
    
        # Try to extract user ID from comment ID
        potential_user_id = self.extract_user_from_comment_id(comment_id)
        if potential_user_id:
            return f"User {potential_user_id[:8]}...", potential_user_id
    
        # Generate name based on comment content
        if comment_message:
            # Use first few characters of message to create a unique identifier
            clean_message = ''.join(c for c in comment_message if c.isalnum())[:8]
            if clean_message:
                return f"Commenter_{clean_message}", ""
    
        # Use comment ID as last resort
        comment_suffix = comment_id.split('_')[-1][:8] if '_' in comment_id else comment_id[:8]
        return f"Anonymous_{comment_suffix}", ""
