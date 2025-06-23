from django.shortcuts import render
from django.http import JsonResponse
from .facebook_api import FacebookGraphAPI
import json

def debug_facebook_api(request):
    """Debug view to check Facebook API permissions and access"""
    
    api = FacebookGraphAPI()
    debug_info = {}
    
    # Check token debug info
    try:
        token_debug = api.debug_token()
        debug_info['token_debug'] = token_debug
    except Exception as e:
        debug_info['token_debug_error'] = str(e)
    
    # Check permissions
    try:
        permissions = api.get_my_permissions()
        debug_info['permissions'] = permissions
    except Exception as e:
        debug_info['permissions_error'] = str(e)
    
    # Check pages access
    try:
        pages = api.get_pages()
        debug_info['pages'] = pages
    except Exception as e:
        debug_info['pages_error'] = str(e)
    
    # Test basic me endpoint
    try:
        me_data = api.make_request("me", {"fields": "id,name"})
        debug_info['me_data'] = me_data
    except Exception as e:
        debug_info['me_data_error'] = str(e)
    
    return JsonResponse(debug_info, indent=2)

def test_page_access(request, page_id):
    """Test access to a specific page"""
    
    api = FacebookGraphAPI()
    test_results = {}
    
    # Test basic page info
    try:
        page_info = api.get_page_info(page_id)
        test_results['page_info'] = page_info
    except Exception as e:
        test_results['page_info_error'] = str(e)
    
    # Test posts access
    try:
        posts = api.get_page_posts_simple(page_id)
        test_results['posts'] = posts
    except Exception as e:
        test_results['posts_error'] = str(e)
    
    # Test feed access
    try:
        feed = api.get_page_feed(page_id)
        test_results['feed'] = feed
    except Exception as e:
        test_results['feed_error'] = str(e)
    
    return JsonResponse(test_results, indent=2)
