from django.contrib import admin
from .models import FacebookPage, FacebookPost, FacebookComment, FacebookMessage


@admin.register(FacebookPage)
class FacebookPageAdmin(admin.ModelAdmin):
    list_display = ['name', 'page_id', 'followers_count', 'created_at']
    search_fields = ['name', 'page_id']

@admin.register(FacebookPost)
class FacebookPostAdmin(admin.ModelAdmin):
    list_display = ['post_id', 'page', 'likes_count', 'comments_count', 'shares_count', 'created_time']
    list_filter = ['page', 'created_time']
    search_fields = ['post_id', 'message']

@admin.register(FacebookComment)
class FacebookCommentAdmin(admin.ModelAdmin):
    list_display = ['comment_id', 'from_name', 'post', 'created_time']
    list_filter = ['created_time']
    search_fields = ['from_name', 'message']

@admin.register(FacebookMessage)
class FacebookMessageAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'from_name', 'page', 'created_time']
    list_filter = ['page', 'created_time']
    search_fields = ['from_name', 'message']
    

