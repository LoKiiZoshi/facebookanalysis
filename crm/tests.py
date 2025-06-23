from django.db import models
from django.utils import timezone

class FacebookPage(models.Model):
    page_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    followers_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class FacebookPost(models.Model):
    post_id = models.CharField(max_length=100, unique=True)
    page = models.ForeignKey(FacebookPage, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    created_time = models.DateTimeField()
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Post {self.post_id}"

class FacebookComment(models.Model):
    comment_id = models.CharField(max_length=100, unique=True)
    post = models.ForeignKey(FacebookPost, on_delete=models.CASCADE)
    message = models.TextField()
    from_name = models.CharField(max_length=200)
    from_id = models.CharField(max_length=100)
    created_time = models.DateTimeField()
    
    def __str__(self):
        return f"Comment by {self.from_name}"

class FacebookMessage(models.Model):
    message_id = models.CharField(max_length=100, unique=True)
    page = models.ForeignKey(FacebookPage, on_delete=models.CASCADE)
    from_name = models.CharField(max_length=200)
    from_id = models.CharField(max_length=100)
    message = models.TextField()
    created_time = models.DateTimeField()
    
    def __str__(self):
        return f"Message from {self.from_name}"
