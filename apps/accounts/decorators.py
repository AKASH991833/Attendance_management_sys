"""
Custom decorators for authentication and authorization
"""
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required as django_login_required
from django.shortcuts import redirect
from django.conf import settings


def teacher_login_required(function=None, login_url=None):
    """
    Custom login_required decorator that also ensures user has a Teacher profile.
    Works like Django's login_required but checks for teacher profile.
    """
    actual_login_url = login_url or settings.LOGIN_URL
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                # Check if it's an API request
                if request.path.startswith('/api/'):
                    return JsonResponse({'error': 'Authentication required'}, status=403)
                return redirect(actual_login_url)
            
            # Ensure user has a teacher profile
            if not hasattr(request.user, 'teacher'):
                if request.path.startswith('/api/'):
                    return JsonResponse({'error': 'Teacher profile not found'}, status=403)
                return redirect('accounts:logout')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if function:
        return decorator(function)
    return decorator


def teacher_required(view_func):
    """
    Decorator to ensure the user is a teacher (not super admin only).
    """
    @wraps(view_func)
    @django_login_required(login_url='/login/')
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'teacher'):
            if request.path.startswith('/api/'):
                return JsonResponse({'error': 'Teacher profile required'}, status=403)
            return redirect('accounts:logout')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def super_admin_required(view_func):
    """
    Decorator to ensure the user is a super admin.
    """
    @wraps(view_func)
    @django_login_required(login_url='/login/')
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'teacher') or not request.user.teacher.is_super_admin:
            if request.path.startswith('/api/'):
                return JsonResponse({'error': 'Super admin access required'}, status=403)
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def ajax_required(view_func):
    """
    Decorator to ensure the request is an AJAX request.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if request.path.startswith('/api/'):
                return JsonResponse({'error': 'AJAX request required'}, status=400)
            from django.http import HttpResponseBadRequest
            return HttpResponseBadRequest()
        return view_func(request, *args, **kwargs)
    return _wrapped_view
