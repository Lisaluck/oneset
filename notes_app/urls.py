from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'content', views.ContentItemViewSet, basename='content')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'profile', views.UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('api/', views.api_root_view, name='api-root'),
    # API endpoints
    path('api/', include(router.urls)),
    # Template URLs
    path('home/', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('create/', views.create_view, name='create'),
    path('create/item/', views.create_view, name='create_view'), 
    path('logout/', views.custom_logout, name='logout'),
    
    path('item/<int:item_id>/download/', views.download_document_view, name='download_document'),
    path('item/<int:item_id>/preview/', views.preview_document_view, name='preview_document'),
    path('item/<int:item_id>/copy/', views.copy_item_view, name='copy_item'),
    
    path('items/', views.all_items_view, name='all_items'),
    path('item/<int:item_id>/', views.item_detail_view, name='item_detail'),
    path('item/<int:item_id>/edit/', views.edit_item_view, name='edit_item'),
    path('item/<int:item_id>/delete/', views.delete_item_view, name='delete_item'),
    path('item/<int:item_id>/copy/', views.copy_item_view, name='copy_item'),
    path('item/<int:item_id>/toggle-star/', views.toggle_star_view, name='toggle_star'),
    path('item/<int:item_id>/toggle-complete/', views.toggle_complete_view, name='toggle_complete'),
    
]
