import os
import re
import hashlib
import mimetypes
from PIL import Image, IptcImagePlugin
from PIL.ExifTags import TAGS, GPSTAGS
import exifread
from src.geo_intel import GeoIntel

class Extractor:
    """Comprehensive extraction and organization of metadata from images."""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.image = None
        self.metadata = {
            "basic_info": {},
            "file_info": {},
            "exif": {},
            "normalized_exif": {
                "camera": {},
                "author_copyright": {},
                "timestamp": {},
                "technical": {},
                "exposure": {}
            },
            "gps": {
                "has_gps": False,
                "coordinates": None,
                "latitude_dms": "Not found",
                "longitude_dms": "Not found",
                "altitude": "Not found",
                "precision": "Not found",
                "nearest_reference": None,
                "map_links": {},
                "raw": {}
            },
            "iptc": {
                "author": "Not found",
                "creator": "Not found",
                "copyright": "Not found",
                "caption": "Not found",
                "keywords": [],
                "sublocation": "Not found",
                "city": "Not found",
                "province_state": "Not found",
                "country": "Not found",
                "credit": "Not found",
                "source": "Not found",
                "raw": {}
            },
            "xmp": {
                "creator": "Not found",
                "metadata_date": "Not found",
                "create_date": "Not found",
                "modify_date": "Not found",
                "software": "Not found",
                "location": "Not found",
                "copyright": "Not found",
                "document_id": "Not found",
                "instance_id": "Not found",
                "raw_xmp": ""
            },
            "xmp_iptc": {},  # Retained for backwards compatibility
            "raw_exif": {},
            "summary_fields": {}
        }
        
    def extract_all(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
            
        self._extract_file_info()
        
        try:
            self.image = Image.open(self.file_path)
            self._extract_basic_info()
            self._extract_pillow_exif()
            self._extract_exifread()
            self._extract_gps_info()
            self._extract_iptc()
            self._extract_xmp()
            self._build_normalized_exif()
            self._build_summary_fields()
        except Exception as e:
            self.metadata["error"] = str(e)
        finally:
            if self.image:
                try:
                    self.image.close()
                except Exception:
                    pass
            
        return self.metadata
        
    def _extract_file_info(self):
        stat = os.stat(self.file_path)
        size_bytes = stat.st_size
        filename = os.path.basename(self.file_path)
        mime_type, _ = mimetypes.guess_type(self.file_path)
        if not mime_type:
            _, ext = os.path.splitext(filename)
            ext_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp',
                '.tiff': 'image/tiff',
                '.tif': 'image/tiff'
            }
            mime_type = ext_map.get(ext.lower(), 'application/octet-stream')

        self.metadata["file_info"] = {
            "filename": filename,
            "file_size_bytes": size_bytes,
            "file_size_formatted": self._format_size(size_bytes),
            "mime_type": mime_type,
            "sha256": self._generate_hash()
        }

    def _format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024.0:.1f} KB"
        else:
            return f"{size_bytes / (1024.0 * 1024.0):.2f} MB"
        
    def _generate_hash(self):
        sha256 = hashlib.sha256()
        try:
            with open(self.file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256.update(byte_block)
            return sha256.hexdigest()
        except Exception:
            return None

    def _extract_basic_info(self):
        if self.image:
            self.metadata["basic_info"] = {
                "filename": os.path.basename(self.file_path),
                "format": self.image.format or "Unknown",
                "mime_type": self.metadata["file_info"].get("mime_type", "image/jpeg"),
                "mode": self.image.mode,
                "width": self.image.width,
                "height": self.image.height,
                "color_mode": self.image.mode,
                "file_size": self.metadata["file_info"].get("file_size_formatted", "Unknown"),
                "sha256": self.metadata["file_info"].get("sha256", "Unknown")
            }

    def _sanitize_for_json(self, value):
        from PIL.TiffImagePlugin import IFDRational
        if isinstance(value, IFDRational):
            return float(value) if value.denominator != 0 else 0.0
        if isinstance(value, (int, float, str, bool, type(None))):
            return value
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="replace")
            except Exception:
                return str(value)
        if isinstance(value, (list, tuple)):
            return [self._sanitize_for_json(v) for v in value]
        if isinstance(value, dict):
            return {str(k): self._sanitize_for_json(v) for k, v in value.items()}
        return str(value)

    def _extract_pillow_exif(self):
        if not self.image:
            return
            
        try:
            exif_data = self.image.getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    self.metadata["exif"][str(tag)] = self._sanitize_for_json(value)
                    
                # Sub-IFDs: ExifIFD (0x8769), Interop (0xa005)
                if hasattr(exif_data, "get_ifd"):
                    try:
                        exif_sub = exif_data.get_ifd(0x8769)
                        for tag_id, value in exif_sub.items():
                            tag = TAGS.get(tag_id, tag_id)
                            self.metadata["exif"][str(tag)] = self._sanitize_for_json(value)
                    except Exception:
                        pass
        except Exception:
            pass

    def _extract_exifread(self):
        try:
            with open(self.file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                for tag, value in tags.items():
                    if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                        self.metadata["raw_exif"][tag] = str(value)
        except Exception:
            pass

    def _extract_gps_info(self):
        if not self.image:
            return
            
        gps_info = {}
        try:
            exif_data = self.image.getexif()
            if hasattr(exif_data, "get_ifd"):
                gps_ifd = exif_data.get_ifd(0x8825)
                for tag_id, value in gps_ifd.items():
                    tag = GPSTAGS.get(tag_id, tag_id)
                    gps_info[tag] = self._sanitize_for_json(value)
            
            # Fallback to ExifRead tags for GPS if Pillow missed any
            if not gps_info:
                for k, v in self.metadata["raw_exif"].items():
                    if k.startswith("GPS "):
                        tag_name = k.replace("GPS ", "GPS")
                        gps_info[tag_name] = v

            if gps_info:
                self.metadata["gps"]["raw"] = gps_info
                
                # Parse coordinates
                lat = gps_info.get("GPSLatitude")
                lat_ref = gps_info.get("GPSLatitudeRef")
                lon = gps_info.get("GPSLongitude")
                lon_ref = gps_info.get("GPSLongitudeRef")
                
                if lat and lon and lat_ref and lon_ref:
                    decimal_lat = self._convert_to_decimal(lat, lat_ref)
                    decimal_lon = self._convert_to_decimal(lon, lon_ref)
                    
                    if decimal_lat is not None and decimal_lon is not None:
                        self.metadata["gps"]["has_gps"] = True
                        self.metadata["gps"]["coordinates"] = {
                            "latitude": decimal_lat,
                            "longitude": decimal_lon
                        }
                        
                        # DMS representation
                        self.metadata["gps"]["latitude_dms"] = self._format_dms(lat, lat_ref)
                        self.metadata["gps"]["longitude_dms"] = self._format_dms(lon, lon_ref)
                        
                        # Altitude
                        alt = gps_info.get("GPSAltitude")
                        alt_ref = gps_info.get("GPSAltitudeRef", 0)
                        if alt is not None:
                            try:
                                alt_val = float(alt)
                                sign = -1 if str(alt_ref) in ['1', 'Below Sea Level'] else 1
                                self.metadata["gps"]["altitude"] = f"{alt_val * sign:.1f} m"
                            except Exception:
                                self.metadata["gps"]["altitude"] = str(alt)
                                
                        # Precision calculation
                        precision = GeoIntel.calculate_precision(decimal_lat, decimal_lon, gps_info)
                        self.metadata["gps"]["precision"] = precision
                        
                        # Offline Nearest Reference
                        nearest = GeoIntel.find_nearest_reference(decimal_lat, decimal_lon)
                        self.metadata["gps"]["nearest_reference"] = nearest
                        
                        # Map Links
                        links = GeoIntel.get_map_links(decimal_lat, decimal_lon)
                        self.metadata["gps"]["map_links"] = links
        except Exception:
            pass

    def _convert_to_decimal(self, value, ref):
        try:
            if isinstance(value, (tuple, list)) and len(value) == 3:
                d = float(value[0])
                m = float(value[1])
                s = float(value[2])
                dec = d + (m / 60.0) + (s / 3600.0)
                if str(ref).strip().upper() in ['S', 'W']:
                    dec = -dec
                return round(dec, 6)
            elif isinstance(value, (int, float)):
                dec = float(value)
                if str(ref).strip().upper() in ['S', 'W'] and dec > 0:
                    dec = -dec
                return round(dec, 6)
        except Exception:
            pass
        return None

    def _format_dms(self, value, ref):
        try:
            if isinstance(value, (tuple, list)) and len(value) == 3:
                d = int(float(value[0]))
                m = int(float(value[1]))
                s = float(value[2])
                ref_clean = str(ref).strip().upper()
                return f"{d}° {m}' {s:.2f}\" {ref_clean}"
        except Exception:
            pass
        return str(value)

    def _extract_iptc(self):
        try:
            iptc_dict = {}
            if self.image:
                iptc_data = IptcImagePlugin.getiptcinfo(self.image)
                if iptc_data:
                    iptc_dict = iptc_data

            # Decode IPTC tags
            def decode_field(keys):
                for k in keys:
                    if k in iptc_dict and iptc_dict[k]:
                        val = iptc_dict[k]
                        if isinstance(val, (list, tuple)):
                            return ", ".join([v.decode('utf-8', errors='replace') if isinstance(v, bytes) else str(v) for v in val])
                        if isinstance(val, bytes):
                            return val.decode('utf-8', errors='replace')
                        return str(val)
                return "Not found"

            author = decode_field([(2, 80), 'By-line', 'author', 'creator'])
            caption = decode_field([(2, 120), 'Caption/Abstract', 'description'])
            copyright_info = decode_field([(2, 116), 'Copyright Notice', 'copyright'])
            city = decode_field([(2, 90), 'City'])
            sublocation = decode_field([(2, 92), 'Sub-location'])
            state = decode_field([(2, 95), 'Province/State'])
            country = decode_field([(2, 101), 'Country/Primary Location Name'])
            credit = decode_field([(2, 110), 'Credit'])
            source = decode_field([(2, 115), 'Source'])

            keywords = []
            if (2, 25) in iptc_dict:
                raw_kw = iptc_dict[(2, 25)]
                if isinstance(raw_kw, (list, tuple)):
                    for item in raw_kw:
                        keywords.append(item.decode('utf-8', errors='replace') if isinstance(item, bytes) else str(item))
                elif isinstance(raw_kw, bytes):
                    keywords.append(raw_kw.decode('utf-8', errors='replace'))

            self.metadata["iptc"] = {
                "author": author,
                "creator": author if author != "Not found" else "Not found",
                "copyright": copyright_info,
                "caption": caption,
                "keywords": keywords,
                "sublocation": sublocation,
                "city": city,
                "province_state": state,
                "country": country,
                "credit": credit,
                "source": source,
                "raw": {str(k): self._sanitize_for_json(v) for k, v in iptc_dict.items()} if iptc_dict else {}
            }
        except Exception:
            pass

    def _extract_xmp(self):
        try:
            xmp_str = ""
            if self.image and hasattr(self.image, "info"):
                xmp_data = self.image.info.get("XML:com.adobe.xmp") or self.image.info.get("xmp")
                if xmp_data:
                    if isinstance(xmp_data, bytes):
                        xmp_str = xmp_data.decode('utf-8', errors='replace')
                    else:
                        xmp_str = str(xmp_data)

            # Fallback byte scan if Pillow info didn't expose XMP
            if not xmp_str:
                try:
                    with open(self.file_path, "rb") as f:
                        header = f.read(1048576)  # Scan first 1MB for XMP packet
                        start_idx = header.find(b"<x:xmpmeta")
                        if start_idx != -1:
                            end_idx = header.find(b"</x:xmpmeta>", start_idx)
                            if end_idx != -1:
                                xmp_str = header[start_idx:end_idx + 12].decode('utf-8', errors='replace')
                except Exception:
                    pass

            if xmp_str:
                self.metadata["xmp"]["raw_xmp"] = xmp_str[:2000] + "..." if len(xmp_str) > 2000 else xmp_str
                self.metadata["xmp_iptc"]["raw_xmp"] = self.metadata["xmp"]["raw_xmp"]

                # Extract standard XMP fields using robust regex
                def extract_tag(patterns):
                    for pat in patterns:
                        m = re.search(pat, xmp_str, re.IGNORECASE | re.DOTALL)
                        if m:
                            val = m.group(1).strip()
                            # Clean inner XML tags if any
                            clean_val = re.sub(r'<[^>]+>', '', val).strip()
                            if clean_val:
                                return clean_val
                    return "Not found"

                creator = extract_tag([
                    r'<dc:creator>.*?<rdf:li>(.*?)</rdf:li>',
                    r'dc:creator="([^"]+)"',
                    r'<photoshop:Author>(.*?)</photoshop:Author>'
                ])
                software = extract_tag([
                    r'<xmp:CreatorTool>(.*?)</xmp:CreatorTool>',
                    r'xmp:CreatorTool="([^"]+)"'
                ])
                metadata_date = extract_tag([
                    r'<xmp:MetadataDate>(.*?)</xmp:MetadataDate>',
                    r'xmp:MetadataDate="([^"]+)"'
                ])
                create_date = extract_tag([
                    r'<xmp:CreateDate>(.*?)</xmp:CreateDate>',
                    r'xmp:CreateDate="([^"]+)"'
                ])
                modify_date = extract_tag([
                    r'<xmp:ModifyDate>(.*?)</xmp:ModifyDate>',
                    r'xmp:ModifyDate="([^"]+)"'
                ])
                copyright_xmp = extract_tag([
                    r'<dc:rights>.*?<rdf:li>(.*?)</rdf:li>',
                    r'dc:rights="([^"]+)"'
                ])
                city = extract_tag([r'<photoshop:City>(.*?)</photoshop:City>', r'photoshop:City="([^"]+)"'])
                country = extract_tag([r'<photoshop:Country>(.*?)</photoshop:Country>', r'photoshop:Country="([^"]+)"'])
                doc_id = extract_tag([r'<xmpMM:DocumentID>(.*?)</xmpMM:DocumentID>', r'xmpMM:DocumentID="([^"]+)"'])
                inst_id = extract_tag([r'<xmpMM:InstanceID>(.*?)</xmpMM:InstanceID>', r'xmpMM:InstanceID="([^"]+)"'])

                loc_parts = [p for p in [city, country] if p != "Not found"]
                location = ", ".join(loc_parts) if loc_parts else "Not found"

                self.metadata["xmp"].update({
                    "creator": creator,
                    "metadata_date": metadata_date,
                    "create_date": create_date,
                    "modify_date": modify_date,
                    "software": software,
                    "location": location,
                    "copyright": copyright_xmp,
                    "document_id": doc_id,
                    "instance_id": inst_id
                })
        except Exception:
            pass

    def _build_normalized_exif(self):
        exif = self.metadata.get("exif", {})
        raw_exif = self.metadata.get("raw_exif", {})

        def get_field(keys, default="Not found"):
            for k in keys:
                val = exif.get(k) or raw_exif.get(k)
                if val is not None and str(val).strip() and str(val).strip().lower() != "none":
                    return str(val).strip()
            return default

        # Camera
        make = get_field(["Make", "Image Make"])
        model = get_field(["Model", "Image Model"])
        lens_make = get_field(["LensMake", "EXIF LensMake"])
        lens_model = get_field(["LensModel", "EXIF LensModel"])
        lens_spec = get_field(["LensSpecification", "EXIF LensSpecification"])
        body_serial = get_field(["BodySerialNumber", "EXIF BodySerialNumber", "SerialNumber"])
        lens_serial = get_field(["LensSerialNumber", "EXIF LensSerialNumber"])

        # Software
        software = get_field(["Software", "Image Software", "ProcessingSoftware"])

        # Author / Copyright
        artist = get_field(["Artist", "Image Artist"])
        copyright_val = get_field(["Copyright", "Image Copyright"])
        owner_name = get_field(["CameraOwnerName", "EXIF CameraOwnerName"])

        # Timestamp
        date_time = get_field(["DateTime", "Image DateTime"])
        date_time_orig = get_field(["DateTimeOriginal", "EXIF DateTimeOriginal"])
        date_time_dig = get_field(["DateTimeDigitized", "EXIF DateTimeDigitized"])
        offset_time = get_field(["OffsetTime", "EXIF OffsetTime"])

        # Technical & Resolution
        orientation_val = get_field(["Orientation", "Image Orientation"])
        x_res = get_field(["XResolution", "Image XResolution"])
        y_res = get_field(["YResolution", "Image YResolution"])
        res_unit = get_field(["ResolutionUnit", "Image ResolutionUnit"])
        color_space = get_field(["ColorSpace", "EXIF ColorSpace"])

        # Exposure
        exp_time = get_field(["ExposureTime", "EXIF ExposureTime"])
        f_number = get_field(["FNumber", "EXIF FNumber"])
        iso = get_field(["ISOSpeedRatings", "EXIF ISOSpeedRatings", "PhotographicSensitivity"])
        focal_length = get_field(["FocalLength", "EXIF FocalLength"])
        flash = get_field(["Flash", "EXIF Flash"])
        white_balance = get_field(["WhiteBalance", "EXIF WhiteBalance"])
        metering = get_field(["MeteringMode", "EXIF MeteringMode"])
        exp_prog = get_field(["ExposureProgram", "EXIF ExposureProgram"])
        exp_bias = get_field(["ExposureBiasValue", "EXIF ExposureBiasValue"])

        self.metadata["normalized_exif"] = {
            "camera": {
                "make": make,
                "model": model,
                "lens_make": lens_make,
                "lens_model": lens_model,
                "lens_specification": lens_spec,
                "body_serial_number": body_serial,
                "lens_serial_number": lens_serial,
                "software": software
            },
            "author_copyright": {
                "artist": artist,
                "copyright": copyright_val,
                "camera_owner": owner_name
            },
            "timestamp": {
                "datetime": date_time,
                "datetime_original": date_time_orig,
                "datetime_digitized": date_time_dig,
                "timezone_offset": offset_time
            },
            "technical": {
                "orientation": orientation_val,
                "x_resolution": x_res,
                "y_resolution": y_res,
                "resolution_unit": res_unit,
                "color_space": color_space,
                "width": self.metadata["basic_info"].get("width", "Not found"),
                "height": self.metadata["basic_info"].get("height", "Not found")
            },
            "exposure": {
                "exposure_time": exp_time,
                "f_number": f_number,
                "iso": iso,
                "focal_length": focal_length,
                "flash": flash,
                "white_balance": white_balance,
                "metering_mode": metering,
                "exposure_program": exp_prog,
                "exposure_bias": exp_bias
            }
        }

    def _build_summary_fields(self):
        """Build high-level display values with guaranteed 'Not found' fallback."""
        norm = self.metadata["normalized_exif"]
        gps = self.metadata["gps"]
        iptc = self.metadata["iptc"]
        xmp = self.metadata["xmp"]

        # Combined camera
        camera_parts = [p for p in [norm["camera"]["make"], norm["camera"]["model"]] if p != "Not found"]
        camera_summary = " ".join(camera_parts) if camera_parts else "Not found"

        # Combined author
        author_cands = [norm["author_copyright"]["artist"], iptc["author"], xmp["creator"]]
        author_valid = [a for a in author_cands if a != "Not found"]
        author_summary = author_valid[0] if author_valid else "Not found"

        # Combined copyright
        copy_cands = [norm["author_copyright"]["copyright"], iptc["copyright"], xmp["copyright"]]
        copy_valid = [c for c in copy_cands if c != "Not found"]
        copyright_summary = copy_valid[0] if copy_valid else "Not found"

        # Combined date
        date_cands = [norm["timestamp"]["datetime_original"], norm["timestamp"]["datetime"], xmp["create_date"]]
        date_valid = [d for d in date_cands if d != "Not found"]
        date_summary = date_valid[0] if date_valid else "Not found"

        # Combined software
        soft_cands = [norm["camera"]["software"], xmp["software"]]
        soft_valid = [s for s in soft_cands if s != "Not found"]
        software_summary = soft_valid[0] if soft_valid else "Not found"

        self.metadata["summary_fields"] = {
            "camera": camera_summary,
            "author": author_summary,
            "copyright": copyright_summary,
            "datetime": date_summary,
            "software": software_summary,
            "gps_exposed": gps["has_gps"]
        }
