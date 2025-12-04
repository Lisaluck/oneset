from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

class ContentItem(models.Model):
    CONTENT_TYPES = [
        ('note', 'Note'),
        ('task', 'Task'),
        ('link', 'Link'),
        ('code', 'Code Snippet'),
        ('document', 'Document'),
    ]
    
    CATEGORIES = [
        ('work', 'Work'),
        ('personal', 'Personal'),
    ]
    
    PRIORITIES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='note')
    category = models.CharField(max_length=20, choices=CATEGORIES, default='personal')
    priority = models.CharField(max_length=10, choices=PRIORITIES, default='medium')
    url = models.URLField(blank=True, null=True)
    file = models.FileField(upload_to='documents/%Y/%m/%d/', blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_file_name(self):
        """Get filename from file path"""
        if self.file:
            return os.path.basename(self.file.name)
        return None
    
    def get_file_extension(self):
        """Get file extension"""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return None
    
    def get_file_size(self):
        """Get human readable file size"""
        if self.file:
            try:
                size = self.file.size
                return self._format_file_size(size)
            except:
                return "Unknown size"
        return None
    
    def _format_file_size(self, size_in_bytes):
        """Convert bytes to human readable format"""
        if size_in_bytes is None:
            return "0 bytes"
        
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.1f} TB"
    
    def get_file_url(self):
        """Get file URL for templates"""
        if self.file:
            try:
                return self.file.url
            except:
                return None
        return None

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('pink', 'Pink Theme'),
        ],
        default='pink'
    )
    storage_used = models.BigIntegerField(default=0)
    items_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} Profile"