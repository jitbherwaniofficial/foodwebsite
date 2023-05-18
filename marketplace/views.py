from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from menu.models import Category, FoodItem

from vendor.models import Vendor
from django.db.models import Prefetch

# Create your views here.


def marketplace(request):
    vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
    vendor_count = vendors.count()
    context = {
        'vendors':vendors,
        'vendor_count':vendor_count,
    }
    return render(request, 'marketplace/listings.html',context)


def vendor_detail(request,vendor_slug):
    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)
    categories = Category.objects.filter(vendor=vendor).prefetch_related(
        Prefetch(
        'fooditems',
        queryset= FoodItem.objects.filter(is_available=True)
        )
    )
    context = {
        'vendor':vendor,
        'categories':categories
    }
    return render(request, 'marketplace/vendor_detail.html', context)


def add_to_cart(request, food_id):
    if request.user.is_authenticated:
        if request.is_ajax():
            #Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # check if the user has already added that food to the cart
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This Food Does Not Exist!'})    
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    else:    
        return JsonResponse({'status': 'Failed', 'message': 'Please login to continue.'})


