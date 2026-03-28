"""Minify CSS and JS files for production."""
import csscompressor
import jsmin
from pathlib import Path


def minify_css():
    """Minify all CSS files in static/css directory."""
    css_dir = Path('static/css')
    if not css_dir.exists():
        print(f"CSS directory not found: {css_dir}")
        return
    
    css_files = list(css_dir.glob('*.css'))
    minified_count = 0
    
    for css_file in css_files:
        if '.min.css' not in css_file.name:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                    minified = csscompressor.compress(original_content)
                
                output = css_file.parent / f"{css_file.stem}.min.css"
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(minified)
                
                original_size = len(original_content)
                minified_size = len(minified)
                savings = 100 - (minified_size * 100 / original_size)
                
                print(f"✓ Minified {css_file.name} → {output.name}")
                print(f"  Size: {original_size:,} → {minified_size:,} bytes ({savings:.1f}% reduction)")
                minified_count += 1
            except Exception as e:
                print(f"✗ Error minifying {css_file.name}: {e}")
    
    print(f"\nMinified {minified_count} CSS files")


def minify_js():
    """Minify all JS files in static/js directory."""
    js_dir = Path('static/js')
    if not js_dir.exists():
        print(f"JS directory not found: {js_dir}")
        return
    
    js_files = list(js_dir.glob('*.js'))
    minified_count = 0
    
    for js_file in js_files:
        if '.min.js' not in js_file.name:
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                    minified = jsmin.jsmin(original_content)
                
                output = js_file.parent / f"{js_file.stem}.min.js"
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(minified)
                
                original_size = len(original_content)
                minified_size = len(minified)
                savings = 100 - (minified_size * 100 / original_size)
                
                print(f"✓ Minified {js_file.name} → {output.name}")
                print(f"  Size: {original_size:,} → {minified_size:,} bytes ({savings:.1f}% reduction)")
                minified_count += 1
            except Exception as e:
                print(f"✗ Error minifying {js_file.name}: {e}")
    
    print(f"\nMinified {minified_count} JS files")


if __name__ == '__main__':
    print("=" * 60)
    print("CSS/JS Minification Tool")
    print("=" * 60)
    print()
    
    print("Minifying CSS files...")
    print("-" * 60)
    minify_css()
    
    print()
    print("Minifying JS files...")
    print("-" * 60)
    minify_js()
    
    print()
    print("=" * 60)
    print("Minification complete!")
    print("=" * 60)
