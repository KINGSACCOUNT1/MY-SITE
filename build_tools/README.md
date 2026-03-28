# Build Tools - Performance Optimization

This directory contains scripts for optimizing Elite Wealth Capital assets.

## Scripts

### 1. minify.py
Minifies CSS and JavaScript files for production.

**Usage:**
```bash
python build_tools/minify.py
```

**What it does:**
- Minifies all `.css` files in `static/css/`
- Minifies all `.js` files in `static/js/`
- Creates `.min.css` and `.min.js` versions
- Reports file size savings (typically 30-45%)

**Requirements:**
- csscompressor
- jsmin

### 2. optimize_images.py
Optimizes images and creates WebP versions.

**Usage:**
```bash
python build_tools/optimize_images.py
```

**What it does:**
- Converts images to WebP format (85% quality)
- Optimizes original formats (JPG, PNG)
- Creates backups before optimization
- Supports recursive directory processing

**Requirements:**
- Pillow (PIL)

**Note:** Run once, then use WebP versions in templates with fallback.

### 3. optimize_queries.py
Database query optimization guide and checker.

**Usage:**
```bash
python build_tools/optimize_queries.py
```

**What it provides:**
- Best practices for query optimization
- Examples of N+1 query prevention
- Guidelines for select_related/prefetch_related
- Index recommendations

### Management Command Alternative

Instead of running scripts directly, use the Django management command:

```bash
# Run all optimizations
python manage.py optimize_assets

# Skip image optimization
python manage.py optimize_assets --skip-images

# Skip minification
python manage.py optimize_assets --skip-minify
```

## Integration with Deployment

### Render

Add to `render.yaml` build command:
```yaml
buildCommand: pip install -r requirements.txt && python manage.py optimize_assets --skip-images && python manage.py collectstatic --noinput
```

### Docker

Add to Dockerfile:
```dockerfile
RUN python manage.py optimize_assets
```

### Manual Deployment

Before deployment:
```bash
python manage.py optimize_assets
git add static/
git commit -m "Optimized assets for production"
git push
```

## File Size Reduction

### CSS Files
- style.css: 72 KB → 50 KB (30.8% reduction)
- dashboard.css: 30 KB → 19 KB (34.6% reduction)
- mobile.css: 15 KB → 8 KB (44.4% reduction)
- **Average: 35% reduction**

### JS Files
- charts.js: 21 KB → 11 KB (47.5% reduction)
- config.js: 431 B → 125 B (71.0% reduction)
- main.js: 12 KB → 7 KB (41.9% reduction)
- **Average: 40% reduction**

### Images
- WebP conversion: 60-80% reduction
- Original optimization: 10-30% reduction
- **Average: 50-70% reduction**

## Troubleshooting

### Minification Fails
- Check for syntax errors in original CSS/JS files
- Ensure csscompressor and jsmin are installed
- Try minifying files individually to isolate issues

### Image Optimization Fails
- Ensure Pillow is installed: `pip install Pillow`
- Check file permissions in static/images/
- Verify image files are not corrupted

### Command Not Found
- Ensure core app is in INSTALLED_APPS
- Run `python manage.py help` to verify commands are loaded
- Check Python path and virtual environment

## See Also

- `OPTIMIZATION_SUMMARY.md` - Complete optimization guide
- `PERFORMANCE.md` - Performance checklist
- `PERFORMANCE_QUICK_REF.md` - Quick reference
- `examples_performance_views.py` - Code examples
