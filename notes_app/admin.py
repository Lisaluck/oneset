from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import ContentItem, UserProfile  # Sirf existing models import karo

class ContentItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'category', 'user', 'is_starred', 'is_completed', 'created_at']
    list_filter = ['content_type', 'category', 'is_starred', 'is_completed', 'created_at']
    search_fields = ['title', 'content', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'content_type', 'category')
        }),
        ('Content Details', {
            'fields': ('content', 'url', 'file', 'language')
        }),
        ('Task Specific', {
            'fields': ('priority', 'due_date', 'is_completed'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('is_starred', 'reminder', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'storage_used', 'items_count']
    list_filter = ['theme']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['storage_used', 'items_count']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'theme')
        }),
        ('Usage Statistics', {
            'fields': ('storage_used', 'items_count'),
            'classes': ('collapse',)
        })
    )

# Register your models here
admin.site.register(ContentItem, ContentItemAdmin)
admin.site.register(UserProfile, UserProfileAdmin)

# Customize admin site
admin.site.site_header = "oneSEt Administration"
admin.site.site_title = "oneSEt Admin Portal"
admin.site.index_title = "Welcome to oneSEt Admin Portal"

# Custom User Admin
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'date_joined', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']

# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)