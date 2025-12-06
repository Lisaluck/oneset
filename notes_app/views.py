from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from .models import ContentItem, UserProfile
from .serializers import UserSerializer, ContentItemSerializer, UserProfileSerializer
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ContentItemForm
from django.http import FileResponse, HttpResponse, JsonResponse
import os
from django.conf import settings

# Template-based views
def home_view(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})
@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'notes': reverse('contentitem-list', request=request, format=format),
        'profile': reverse('userprofile-list', request=request, format=format),
        'login': reverse('rest_framework:login', request=request, format=format),
        'logout': reverse('rest_framework:logout', request=request, format=format),
    })

@login_required
def dashboard_view(request):
    try:
        user = request.user
        
        # Get counts for all item types
        total_items = ContentItem.objects.filter(user=user).count()
        
        # Task counts
        completed_tasks = ContentItem.objects.filter(
            user=user, 
            content_type='task', 
            is_completed=True
        ).count()
        
        total_tasks = ContentItem.objects.filter(
            user=user, 
            content_type='task'
        ).count()
        
        starred_items = ContentItem.objects.filter(
            user=user, 
            is_starred=True
        ).count()
        
        # Counts by type for sidebar
        note_count = ContentItem.objects.filter(
            user=user, 
            content_type='note'
        ).count()
        
        task_count = ContentItem.objects.filter(
            user=user, 
            content_type='task'
        ).count()
        
        link_count = ContentItem.objects.filter(
            user=user, 
            content_type='link'
        ).count()
        
        code_count = ContentItem.objects.filter(
            user=user, 
            content_type='code'
        ).count()
        
        document_count = ContentItem.objects.filter(
            user=user, 
            content_type='document'
        ).count()
        
        # Get recent items
        recent_items = ContentItem.objects.filter(
            user=user
        ).order_by('-created_at')[:6]
        
        context = {
            'total_items': total_items,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'starred_items': starred_items,
            'pending_tasks': total_tasks - completed_tasks,
            'recent_items': recent_items,
            # Add type counts for sidebar
            'note_count': note_count,
            'task_count': task_count,
            'link_count': link_count,
            'code_count': code_count,
            'document_count': document_count,
        }
    except Exception as e:
        print(f"Dashboard error: {e}")
        context = {
            'total_items': 0,
            'completed_tasks': 0,
            'total_tasks': 0,
            'starred_items': 0,
            'pending_tasks': 0,
            'recent_items': [],
            'note_count': 0,
            'task_count': 0,
            'link_count': 0,
            'code_count': 0,
            'document_count': 0,
        }
    
    return render(request, 'dashboard.html', context)

@login_required
def create_view(request):
    if request.method == 'POST':
        try:
            # Create content item with form data
            title = request.POST.get('title')
            content = request.POST.get('content')
            content_type = request.POST.get('content_type')
            category = request.POST.get('category', 'personal')
            priority = request.POST.get('priority', '')
            url = request.POST.get('url', '')
            language = request.POST.get('language', '')
            due_date = request.POST.get('due_date', '')
            is_starred = request.POST.get('is_starred') == 'true'
            tags = request.POST.get('tags', '')
            
            # Create content item
            content_item = ContentItem(
                user=request.user,
                title=title,
                content=content,
                content_type=content_type,
                category=category,
                priority=priority,
                url=url,
                language=language,
                tags=tags,
                is_starred=is_starred
            )
            
            # Set due date if provided
            if due_date:
                from django.utils.dateparse import parse_date
                parsed_due_date = parse_date(due_date)
                if parsed_due_date:
                    content_item.due_date = parsed_due_date
            
            # Handle file upload
            if 'file' in request.FILES:
                content_item.file = request.FILES['file']
            
            content_item.save()
            
            messages.success(request, 'Item created successfully!')
            return redirect('item_detail', item_id=content_item.id)
            
        except Exception as e:
            messages.error(request, f'Error creating item: {str(e)}')
            return render(request, 'create.html')
    
    # GET request - show empty form
    return render(request, 'create.html')

def custom_logout(request):
    logout(request)
    return redirect('home')

@login_required 
def all_items_view(request):
    """View all items with filtering and pagination"""
    content_type = request.GET.get('type', '')
    category = request.GET.get('category', '')
    starred = request.GET.get('starred', '')
    
    items = ContentItem.objects.filter(user=request.user)
    
    # Apply filters
    if content_type:
        items = items.filter(content_type=content_type)
    if category:
        items = items.filter(category=category)
    if starred == 'true':
        items = items.filter(is_starred=True)
    
    # Debug के लिए
    print(f"Total items: {items.count()}")
    for item in items:
        print(f"Item ID: {item.id}, Title: {item.title}")
    
    # Get counts for filters
    total_count = items.count()
    note_count = ContentItem.objects.filter(user=request.user, content_type='note').count()
    task_count = ContentItem.objects.filter(user=request.user, content_type='task').count()
    link_count = ContentItem.objects.filter(user=request.user, content_type='link').count()
    code_count = ContentItem.objects.filter(user=request.user, content_type='code').count()
    document_count = ContentItem.objects.filter(user=request.user, content_type='document').count()
    
    context = {
        'items': items,
        'total_count': total_count,
        'note_count': note_count,
        'task_count': task_count,
        'link_count': link_count,
        'code_count': code_count,
        'document_count': document_count,
        'current_type': content_type,
        'current_category': category,
        'current_starred': starred,
    }
    return render(request, 'all_items.html', context)

@login_required
def item_detail_view(request, item_id):
    """View individual item details"""
    item = get_object_or_404(ContentItem, id=item_id, user=request.user)
    
    # Debugging के लिए ये print करें
    print(f"=== DEBUG ITEM DETAIL ===")
    print(f"Item ID: {item.id}")
    print(f"Item Title: {item.title}")
    print(f"Item Type: {item.content_type}")
    print(f"Has File: {item.file}")
    print(f"File object: {item.file}")
    
    if item.file:
        print(f"File name: {item.file.name}")
        print(f"File URL: {item.file.url}")
        print(f"File path: {item.file.path}")
        print(f"File exists: {os.path.exists(item.file.path)}")
    
    return render(request, 'item_detail.html', {'item': item})

@login_required
def edit_item_view(request, item_id):
    """Edit an existing item"""
    item = get_object_or_404(ContentItem, id=item_id, user=request.user)
    
    if request.method == 'POST':
        try:
            item.title = request.POST.get('title')
            item.content = request.POST.get('content')
            item.content_type = request.POST.get('content_type')
            item.category = request.POST.get('category', 'personal')
            item.priority = request.POST.get('priority', '')
            item.url = request.POST.get('url', '')
            item.language = request.POST.get('language', '')
            item.tags = request.POST.get('tags', '')
            item.is_starred = request.POST.get('is_starred') == 'true'
            
            # Handle due date
            due_date = request.POST.get('due_date', '')
            if due_date:
                from django.utils.dateparse import parse_date
                parsed_due_date = parse_date(due_date)
                if parsed_due_date:
                    item.due_date = parsed_due_date
            
            # Handle file upload
            if 'file' in request.FILES:
                # Delete old file if exists
                if item.file:
                    if os.path.isfile(item.file.path):
                        os.remove(item.file.path)
                item.file = request.FILES['file']
            
            # Handle task completion
            if item.content_type == 'task':
                item.is_completed = request.POST.get('is_completed') == 'true'
            
            item.save()
            messages.success(request, 'Item updated successfully!')
            return redirect('item_detail', item_id=item.id)
            
        except Exception as e:
            messages.error(request, f'Error updating item: {str(e)}')
    
    return render(request, 'edit_item.html', {'item': item})

@login_required
def delete_item_view(request, item_id):
    """Delete an item"""
    item = get_object_or_404(ContentItem, id=item_id, user=request.user)
    
    if request.method == 'POST':
        # Delete associated file if exists
        if item.file:
            if os.path.isfile(item.file.path):
                os.remove(item.file.path)
        item.delete()
        messages.success(request, 'Item deleted successfully!')
        return redirect('all_items')
    
    return render(request, 'confirm_delete.html', {'item': item})

@login_required
def copy_item_view(request, item_id):
    """Create a copy of an item"""
    original_item = get_object_or_404(ContentItem, id=item_id, user=request.user)
    
    # Create a copy without the file first
    copied_item = ContentItem(
        user=request.user,
        title=f"Copy of {original_item.title}",
        content=original_item.content,
        content_type=original_item.content_type,
        category=original_item.category,
        priority=original_item.priority,
        url=original_item.url,
        language=original_item.language,
        tags=original_item.tags,
        is_starred=False,  # Don't copy starred status
        is_completed=False,  # Don't copy completion status
    )
    
    # Copy due date
    if original_item.due_date:
        copied_item.due_date = original_item.due_date
    
    copied_item.save()
    
    messages.success(request, 'Item copied successfully!')
    return redirect('item_detail', item_id=copied_item.id)

@login_required
def toggle_star_view(request, item_id):
    """Toggle star status"""
    item = get_object_or_404(ContentItem, id=item_id, user=request.user)
    item.is_starred = not item.is_starred
    item.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_starred': item.is_starred})
    
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def toggle_complete_view(request, item_id):
    """Toggle completion status for tasks"""
    item = get_object_or_404(ContentItem, id=item_id, user=request.user)
    if item.content_type == 'task':
        item.is_completed = not item.is_completed
        item.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_completed': item.is_completed})
    
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def download_document_view(request, item_id):
    """Download document file"""
    item = get_object_or_404(ContentItem, id=item_id, user=request.user)
    
    if item.file:
        try:
            # For security, serve file through Django
            response = FileResponse(item.file.open(), as_attachment=True)
            
            # Get filename properly
            filename = os.path.basename(item.file.name)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Set appropriate content type
            file_extension = os.path.splitext(filename)[1].lower()
            content_types = {
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.txt': 'text/plain',
                '.csv': 'text/csv',
            }
            
            if file_extension in content_types:
                response['Content-Type'] = content_types[file_extension]
            
            return response
        except Exception as e:
            print(f"Download error: {e}")
            messages.error(request, f"Error downloading file: {str(e)}")
    
    messages.error(request, "File not found")
    return redirect('item_detail', item_id=item_id)

@login_required
def preview_document_view(request, item_id):
    """Preview document (for PDF and images)"""
    item = get_object_or_404(ContentItem, id=item_id, user=request.user)
    
    # Check if file exists safely
    if item.file and hasattr(item.file, 'name'):
        try:
            if item.file.name:
                try:
                    file_extension = os.path.splitext(item.file.name)[1].lower()
                    
                    # Only allow preview for certain file types
                    if file_extension in ['.pdf', '.jpg', '.jpeg', '.png', '.gif']:
                        try:
                            response = FileResponse(item.file.open())
                            
                            if file_extension == '.pdf':
                                response['Content-Type'] = 'application/pdf'
                                response['Content-Disposition'] = f'inline; filename="{os.path.basename(item.file.name)}"'
                            elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                                response['Content-Type'] = f'image/{file_extension[1:]}'
                                response['Content-Disposition'] = 'inline'
                            
                            return response
                        except ValueError:
                            return HttpResponse("File exists but cannot be opened", status=500)
                    else:
                        return HttpResponse("Preview not available for this file type", status=400)
                except AttributeError:
                    return HttpResponse("Invalid file", status=400)
        except ValueError:
            return HttpResponse("No file attached", status=404)
    
    return HttpResponse("File not found", status=404)

@login_required
def upload_file_view(request, item_id):
    """Handle file upload via AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        item = get_object_or_404(ContentItem, id=item_id, user=request.user)
        
        if 'file' in request.FILES:
            try:
                # Delete old file if exists
                if item.file:
                    if os.path.isfile(item.file.path):
                        os.remove(item.file.path)
                
                # Save new file
                item.file = request.FILES['file']
                item.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'File uploaded successfully',
                    'file_url': item.file.url if item.file else None,
                    'file_name': item.get_file_name(),
                    'file_size': item.get_file_size()
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
        
        return JsonResponse({
            'success': False,
            'error': 'No file provided'
        }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)

# API Views (REST Framework)
class ContentItemViewSet(viewsets.ModelViewSet):
    serializer_class = ContentItemSerializer
    
    def get_queryset(self):
        return ContentItem.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        # Update user profile count
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        profile.items_count = ContentItem.objects.filter(user=self.request.user).count()
        profile.save()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not username or not password:
                return Response(
                    {'error': 'Username and password are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if User.objects.filter(username=username).exists():
                return Response(
                    {'error': 'Username already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=password
            )
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            login(request, user)
            
            return Response({
                'message': 'User created successfully', 
                'user_id': user.id,
                'username': user.username
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
