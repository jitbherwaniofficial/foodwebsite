from django.shortcuts import get_object_or_404, render
from accounts.forms import UserProfileForm

from vendor.forms import VendorForm

# Create your views here.

def vprofile(request):

    profile = get_object_or_404()

    profile_form = UserProfileForm()
    vendor_form = VendorForm()
    context = {
        'profile_form': profile_form,
        'vendor_form': vendor_form
    }

    return render(request, 'vendor/vprofile.html', context)