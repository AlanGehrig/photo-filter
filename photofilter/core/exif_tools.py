"""EXIF metadata reading and batch rename."""
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS


class ExifReader:
    """Read EXIF metadata from photos."""
    
    # Common EXIF fields
    COMMON_TAGS = {
        'DateTimeOriginal': '拍摄时间',
        'Make': '相机厂商',
        'Model': '相机型号',
        'LensModel': '镜头',
        'FocalLength': '焦距',
        'FNumber': '光圈',
        'ExposureTime': '快门',
        'ISO': 'ISO',
        'GPSInfo': 'GPS',
        'ImageWidth': '宽度',
        'ImageHeight': '高度',
        'Orientation': '方向',
    }
    
    def read(self, photo) -> dict:
        """Read EXIF data from photo."""
        result = {
            'path': str(photo.path),
            'filename': photo.path.name,
            'exists': False,
        }
        
        try:
            img = Image.open(photo.path)
            exif = img._getexif()
            
            if not exif:
                return result
            
            result['exists'] = True
            
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    continue
                result[tag] = value
            
            # Extract common fields
            if 'DateTimeOriginal' in result:
                result['date_taken'] = result['DateTimeOriginal']
            elif 'DateTime' in result:
                result['date_taken'] = result['DateTime']
            
            # Camera info
            make = result.get('Make', '')
            model = result.get('Model', '')
            if make and model:
                result['camera'] = f"{make} {model}"
            elif model:
                result['camera'] = model
            
            # Format values
            if 'FNumber' in result:
                result['aperture'] = f"f/{result['FNumber']}"
            
            if 'ExposureTime' in result:
                exp = result['ExposureTime']
                if exp < 1:
                    result['shutter'] = f"1/{int(1/exp)}s"
                else:
                    result['shutter'] = f"{exp}s"
            
            if 'FocalLength' in result:
                result['focal'] = f"{result['FocalLength']}mm"
            
            if 'ISO' in result:
                result['iso'] = f"ISO {result['ISO']}"
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def read_batch(self, photos) -> list:
        """Read EXIF from multiple photos."""
        return [self.read(p) for p in photos]
    
    def get_date(self, exif_data: dict) -> str:
        """Extract date from EXIF for naming."""
        date_str = exif_data.get('date_taken') or exif_data.get('DateTimeOriginal')
        if date_str:
            try:
                dt = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                return dt.strftime('%Y%m%d_%H%M%S')
            except:
                pass
        
        # Fallback to file modification time
        return datetime.now().strftime('%Y%m%d_%H%M%S')


class BatchRenamer:
    """Batch rename photos with pattern support."""
    
    PATTERN_VARS = {
        '{n}': '序号 (1, 2, 3...)',
        '{n:03d}': '序号补零 (001, 002...)',
        '{date}': '日期 (20260313)',
        '{datetime}': '日期时间',
        '{year}': '年',
        '{month}': '月',
        '{day}': '日',
        '{camera}': '相机型号',
        '{original}': '原文件名',
    }
    
    def __init__(self):
        self.exif_reader = ExifReader()
    
    def preview(self, photos, pattern, exif_data=None) -> list:
        """Preview rename results."""
        if exif_data is None:
            exif_data = self.exif_reader.read_batch(photos)
        
        results = []
        
        for i, (photo, exif) in enumerate(zip(photos, exif_data)):
            new_name = self._apply_pattern(
                photo, 
                pattern, 
                i + 1, 
                exif
            )
            results.append({
                'original': photo.path.name,
                'new': new_name,
                'path': str(photo.path),
            })
        
        return results
    
    def _apply_pattern(self, photo, pattern, index, exif_data: dict) -> str:
        """Apply rename pattern."""
        import re
        
        # Number with padding
        def get_number(m):
            padding = len(m.group(1))
            return f"{index:0{padding}d}" if padding else str(index)
        
        result = re.sub(r'\{n:(\d+)d\}', get_number, pattern)
        result = result.replace('{n}', str(index))
        
        # Date variables
        date_str = self.exif_reader.get_date(exif_data)
        result = result.replace('{datetime}', date_str)
        result = result.replace('{date}', date_str[:8])
        
        try:
            dt = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
            result = result.replace('{year}', str(dt.year))
            result = result.replace('{month}', f"{dt.month:02d}")
            result = result.replace('{day}', f"{dt.day:02d}")
        except:
            result = result.replace('{year}', '')
            result = result.replace('{month}', '')
            result = result.replace('{day}', '')
        
        # Original filename
        result = result.replace('{original}', photo.path.stem)
        
        # Camera
        camera = exif_data.get('camera', '').replace(' ', '_')
        result = result.replace('{camera}', camera)
        
        # Add extension
        if '.' not in result:
            result += photo.path.suffix
        
        return result
    
    def execute(self, photos, pattern) -> dict:
        """Execute batch rename."""
        exif_data = self.exif_reader.read_batch(photos)
        preview = self.preview(photos, pattern, exif_data)
        
        success = 0
        failed = 0
        errors = []
        
        for item in preview:
            try:
                old_path = Path(item['path'])
                new_path = old_path.parent / item['new']
                
                # Handle name conflicts
                if new_path.exists() and new_path != old_path:
                    base = new_path.stem
                    ext = new_path.suffix
                    counter = 1
                    while new_path.exists():
                        new_path = new_path.parent / f"{base}_{counter}{ext}"
                        counter += 1
                
                old_path.rename(new_path)
                success += 1
            except Exception as e:
                failed += 1
                errors.append(f"{item['original']}: {e}")
        
        return {
            'success': success,
            'failed': failed,
            'errors': errors,
        }
