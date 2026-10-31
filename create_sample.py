import os
from PIL import Image
import piexif

def create_sample_image():
    # Create images dir if not exists
    os.makedirs("images", exist_ok=True)
    
    # Create a basic image
    img = Image.new('RGB', (100, 100), color = 'red')
    
    # EXIF data structure
    zeroth_ifd = {
        piexif.ImageIFD.Make: b"Apple",
        piexif.ImageIFD.Model: b"iPhone 12",
        piexif.ImageIFD.Software: b"Adobe Photoshop",
        piexif.ImageIFD.Artist: b"John Doe",
        piexif.ImageIFD.Copyright: b"John Doe"
    }
    
    exif_ifd = {
        piexif.ExifIFD.DateTimeOriginal: b"2023:10:01 12:00:00",
        piexif.ExifIFD.BodySerialNumber: b"123456789"
    }
    
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: b'N',
        piexif.GPSIFD.GPSLatitude: ((40, 1), (42, 1), (4600, 100)), # 40 deg 42 min 46 sec
        piexif.GPSIFD.GPSLongitudeRef: b'W',
        piexif.GPSIFD.GPSLongitude: ((74, 1), (0, 1), (2100, 100)) # 74 deg 0 min 21 sec
    }
    
    exif_dict = {"0th": zeroth_ifd, "Exif": exif_ifd, "GPS": gps_ifd}
    exif_bytes = piexif.dump(exif_dict)
    
    img.save("images/sample.jpg", "jpeg", exif=exif_bytes)
    print("Sample image created at images/sample.jpg")

if __name__ == "__main__":
    create_sample_image()
