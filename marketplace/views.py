from datetime import date, datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from marketplace.context_processors import get_cart_amounts, get_cart_counter
from marketplace.models import Cart
from menu.models import Category, FoodItem
from orders.forms import OrderForm

from vendor.models import OpeningHour, Vendor
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D  # ``D`` is a shortcut for ``Distance``
from django.contrib.gis.db.models.functions import Distance
from accounts.models import UserProfile

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

    opening_hours = OpeningHour.objects.filter(vendor=vendor).order_by('day', 'from_hour')

    # CHECK CURRENT DAY'S OPENING HOURS
    today = date.today().isoweekday()
    current_opening_hours = OpeningHour.objects.filter(vendor=vendor, day=today)

    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
    else:
        cart_items = None    
    context = {
        'vendor':vendor,
        'categories':categories,
        'cart_items':cart_items,
        'opening_hours':opening_hours,
        'current_opening_hours':current_opening_hours,
    }
    return render(request, 'marketplace/vendor_detail.html', context)


def add_to_cart(request, food_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            #Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # check if the user has already added that food to the cart
                try:
                    check_cart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    # Increase CART quantity
                    check_cart.quantity += 1
                    check_cart.save()
                    return JsonResponse({'status': 'Success', 'message': 'Cart Quantity Increased!', 'cart_counter': get_cart_counter(request), 'qty': check_cart.quantity, 'cart_amount': get_cart_amounts(request)})
                except:
                    check_cart = Cart.objects.create(user=request.user, fooditem=fooditem, quantity=1)    
                    return JsonResponse({'status': 'Success', 'message': 'Added the food to the cart!', 'cart_counter': get_cart_counter(request), 'qty': check_cart.quantity, 'cart_amount': get_cart_amounts(request)})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This Food Does Not Exist!'})    
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    else:    
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue.'})



def decrease_cart(request, food_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            #Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # check if the user has already added that food to the cart
                try:
                    check_cart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    if check_cart.quantity > 1:
                    # Decrease CART quantity
                        check_cart.quantity -= 1
                        check_cart.save()
                    else:
                        check_cart.delete()    
                        check_cart.quantity = 0
                    return JsonResponse({'status': 'Success', 'cart_counter': get_cart_counter(request), 'qty': check_cart.quantity, 'cart_amount': get_cart_amounts(request)})
                except:
                    return JsonResponse({'status': 'Failed', 'message': 'You do not have this item in your cart!',})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This Food Does Not Exist!'})    
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    else:    
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue.'})


@login_required(login_url='login')
def cart(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    context = {
        'cart_items':cart_items,
    }
    return render(request, 'marketplace/cart.html',context)


def delete_cart(request, cart_id):    
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                # CHECK IF THE CART ITEM EXIST
                cart_item = Cart.objects.get(user=request.user, id=cart_id)
                if cart_item:
                    cart_item.delete()
                    return JsonResponse({'status': 'Success', 'message': 'Cart item has been deleted!', 'cart_counter': get_cart_counter(request),'cart_amount': get_cart_amounts(request)})
            except:
                 return JsonResponse({'status': 'Failed', 'message': 'Cart item Does Not Exist!'}) 
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})



def search(request):
    if not 'address' in request.GET:
        return redirect('marketplace') 
    else:    
        address = request.GET['add']
        latitude = request.GET['lat']
        longitude = request.GET['lng']
        radius = request.GET['radius']
        keyword = request.GET['keyword']

        # get vendor ids that has food item the user is looking for
        fetch_vendors_by_food_items = FoodItem.objects.filter(food_title__icontains=keyword, is_available=True).values_list('vendor', flat=True) 

        vendors = Vendor.objects.filter(Q(id__in=fetch_vendors_by_food_items) | Q(vendor_name__icontains=keyword, is_approved=True, user__is_active=True))
        if latitude and longitude and radius:
            pnt = GEOSGeometry('POINT(%s %s)' % (longitude, latitude))
            vendors = Vendor.objects.filter(Q(id__in=fetch_vendors_by_food_items) | Q(vendor_name__icontains=keyword, is_approved=True, user__is_active=True), 
            user_profile__location__distance_lte=(pnt, D(km=radius))
            ).annotate(distance=Distance('user_profile__location', pnt)).order_by('distance')

            for v in vendors:
                v.kms = round(v.distance.km,1)

        vendor_count = vendors.count()
        context = {
            'vendors': vendors,
            'vendor_count': vendor_count,
            'source_location':address
        }

        return render(request, 'marketplace/listings.html', context)
    

@login_required(login_url='login')
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('marketplace')
    
    user_profile = UserProfile.objects.get(user=request.user)
    default_values = {
        'first_name':request.user.first_name,
        'last_name':request.user.last_name,
        'phone':request.user.phone_number,
        'email':request.user.email,
        'address':user_profile.address,
        'country':user_profile.country,
        'state':user_profile.state,
        'city':user_profile.city,
        'pin_code':user_profile.pin_code,
    }
    form = OrderForm(initial=default_values)
    context = {
        'form':form,
        'cart_items':cart_items
    }
    return render(request, 'marketplace/checkout.html',context)