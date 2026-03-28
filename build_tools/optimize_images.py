"""Optimize images for web performance."""
from PIL import Image
from pathlib import Path
import os


def optimize_images():
    """Optimize images in static/images directory."""
    image_dir = Path('static/images')
    if not image_dir.exists():
        print(f"Image directory not found: {image_dir}")
        return
    
    # Supported formats
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    optimized_count = 0
    webp_count = 0
    
    for ext in image_extensions:
        for img_path in image_dir.glob(f'**/{ext}'):
            try:
                # Skip if already optimized (check for .webp sibling)
                webp_path = img_path.with_suffix('.webp')
                
                # Open image
                with Image.open(img_path) as img:
                    original_size = img_path.stat().st_size
                    
                    # Convert to RGB if necessary (for JPEG conversion)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # For transparent images, keep RGBA for WebP
                        if not webp_path.exists():
                            img.save(webp_path, 'WEBP', quality=85, optimize=True)
                            webp_size = webp_path.stat().st_size
                            webp_savings = 100 - (webp_size * 100 / original_size)
                            print(f"✓ Created WebP: {webp_path.name}")
                            print(f"  Size: {original_size:,} → {webp_size:,} bytes ({webp_savings:.1f}% reduction)")
                            webp_count += 1
                    else:
                        # Convert to RGB for JPEG optimization
                        rgb_img = img.convert('RGB')
                        
                        # Create WebP version
                        if not webp_path.exists():
                            rgb_img.save(webp_path, 'WEBP', quality=85, optimize=True)
                            webp_size = webp_path.stat().st_size
                            webp_savings = 100 - (webp_size * 100 / original_size)
                            print(f"✓ Created WebP: {webp_path.name}")
                            print(f"  Size: {original_size:,} → {webp_size:,} bytes ({webp_savings:.1f}% reduction)")
                            webp_count += 1
                        
                        # Optimize original (create backup first)
                        backup_path = img_path.with_suffix(img_path.suffix + '.bak')
                        if not backup_path.exists():
                            # Save backup
                            img.save(backup_path)
                            
                            # Optimize original
                            if img_path.suffix.lower() in ['.jpg', '.jpeg']:
                                rgb_img.save(img_path, 'JPEG', quality=85, optimize=True)
                            elif img_path.suffix.lower() == '.png':
                                img.save(img_path, 'PNG', optimize=True)
                            
                            optimized_size = img_path.stat().st_size
                            savings = 100 - (optimized_size * 100 / original_size)
                            
                            print(f"✓ Optimized: {img_path.name}")
                            print(f"  Size: {original_size:,} → {optimized_size:,} bytes ({savings:.1f}% reduction)")
                            optimized_count += 1
                
            except Exception as e:
                print(f"✗ Error processing {img_path.name}: {e}")
    
    print(f"\nOptimized {optimized_count} images")
    print(f"Created {webp_count} WebP versions")


if __name__ == '__main__':
    print("=" * 60)
    print("Image Optimization Tool")
    print("=" * 60)
    print()
    
    optimize_images()
    
    print()
    print("=" * 60)
    print("Optimization complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Update templates to use WebP with fallback")
    print("2. Add loading='lazy' to image tags")
    print("3. Use responsive srcset attributes")
