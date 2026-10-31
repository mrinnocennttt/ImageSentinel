import os
from PIL import Image
import piexif

class Sanitizer:
    """Removes sensitive metadata (EXIF, IPTC, XMP, MakerNotes) from images."""
    
    def __init__(self, file_path, output_dir):
        self.file_path = file_path
        self.output_dir = output_dir
        
    def sanitize(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
            
        os.makedirs(self.output_dir, exist_ok=True)
        filename = os.path.basename(self.file_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(self.output_dir, f"{name}_clean{ext}")
        
        try:
            with Image.open(self.file_path) as image:
                orig_format = image.format or "JPEG"

                # Check if image mode needs conversion for JPEG saving
                save_mode = image.mode
                if orig_format.upper() in ['JPEG', 'JPG'] and save_mode in ['RGBA', 'P', 'LA']:
                    # Convert transparent or paletted images to RGB for clean JPEG saving
                    clean_img = Image.new('RGB', image.size, (255, 255, 255))
                    if save_mode == 'RGBA':
                        clean_img.paste(image, mask=image.split()[3])
                    else:
                        clean_img.paste(image.convert('RGB'))
                else:
                    # Strip metadata via pixel reconstruction
                    clean_img = Image.new(image.mode, image.size)
                    if hasattr(image, "get_flattened_data"):
                        pixel_data = list(image.get_flattened_data())
                    else:
                        pixel_data = list(image.getdata())
                    clean_img.putdata(pixel_data)

                # Save clean image without any metadata headers
                save_kwargs = {}
                fmt_upper = orig_format.upper()
                if fmt_upper in ['JPEG', 'JPG']:
                    save_kwargs['quality'] = 98
                    save_kwargs['optimize'] = True
                elif fmt_upper == 'PNG':
                    save_kwargs['optimize'] = True
                    save_kwargs['pnginfo'] = None
                elif fmt_upper == 'WEBP':
                    save_kwargs['quality'] = 98

                clean_img.save(output_path, format=orig_format, **save_kwargs)

                # For JPEG and TIFF, additionally attempt piexif removal if available
                if fmt_upper in ['JPEG', 'JPG', 'TIFF']:
                    try:
                        piexif.remove(output_path)
                    except Exception:
                        pass
                
            return output_path
        except Exception as e:
            raise Exception(f"Sanitization failed: {str(e)}")
