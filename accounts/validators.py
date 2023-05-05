import os
from django.core.exceptions import ValidationError

def allow_only_images_validator(value):
    ext = os.path.splitext(value.name)[1]
    print(ext)
    valid_extension = ['.png', '.jpg', '.jpeg','.pdf']
    if not ext.lower() in valid_extension:
        raise ValidationError('Unsupported File Extension. Allowed extensions: '+ str(valid_extension))