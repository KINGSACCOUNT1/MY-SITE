# Placeholder Images Created

This directory contains image placeholders for the Elite Wealth Capita platform.

## Images to Replace

### Logo Files
- **logo.svg** - Main company logo (placeholder SVG)
- **logo-dark.svg** - Dark theme logo (create copy of logo.svg with dark colors)

### Avatar Images
Create 300x300px images for:
- avatar-1.jpg - Testimonial avatar 1
- avatar-2.jpg - Testimonial avatar 2
- avatar-3.jpg - Testimonial avatar 3
- avatar-4.jpg - Testimonial avatar 4
- avatar-5.jpg - Testimonial avatar 5
- avatar-6.jpg - Testimonial avatar 6

### Team Member Images
Create 400x500px professional photos for:
- team/john-smith.jpg - CEO
- team/sarah-johnson.jpg - CTO
- team/michael-patel.jpg - CFO

### Office Location Images
Create 800x600px photos for:
- offices/office-ny.jpg - New York headquarters
- offices/office-london.jpg - London office
- offices/office-singapore.jpg - Singapore office

### Partner Logos
Create 200x100px PNG logos with transparency for:
- partners/partner-1.png - Through partner-6.png

## Quick Placeholder Generation

Using ImageMagick or similar tools:

```bash
# Create avatar placeholder
convert -size 300x300 xc:#F59E0B -pointsize 100 -fill white -gravity center \
  -annotate +0+0 "👤" avatar-1.jpg

# Create team photo placeholder
convert -size 400x500 xc:#3B82F6 -pointsize 60 -fill white -gravity center \
  -annotate +0+0 "Team Member" team/john-smith.jpg

# Create office placeholder
convert -size 800x600 xc:#1E3A8A -pointsize 40 -fill white -gravity center \
  -annotate +0+0 "Office Location" offices/office-ny.jpg

# Create partner logo placeholder
convert -size 200x100 xc:white -pointsize 30 -fill "#F59E0B" -gravity center \
  -annotate +0+0 "Partner" partners/partner-1.png
```

## File Structure After Adding Images

```
assets/images/
├── logo.svg (PLACEHOLDER - replace with actual logo)
├── logo-dark.svg (PLACEHOLDER - replace with actual dark logo)
├── hero-background.jpg (TODO - add 1920x1080 hero image)
├── avatars/
│   ├── avatar-1.jpg (PLACEHOLDER)
│   ├── avatar-2.jpg (PLACEHOLDER)
│   ├── avatar-3.jpg (PLACEHOLDER)
│   ├── avatar-4.jpg (PLACEHOLDER)
│   ├── avatar-5.jpg (PLACEHOLDER)
│   └── avatar-6.jpg (PLACEHOLDER)
├── team/
│   ├── john-smith.jpg (TODO - CEO)
│   ├── sarah-johnson.jpg (TODO - CTO)
│   └── michael-patel.jpg (TODO - CFO)
├── offices/
│   ├── office-ny.jpg (TODO - New York)
│   ├── office-london.jpg (TODO - London)
│   └── office-singapore.jpg (TODO - Singapore)
└── partners/
    ├── partner-1.png (TODO)
    ├── partner-2.png (TODO)
    ├── partner-3.png (TODO)
    ├── partner-4.png (TODO)
    ├── partner-5.png (TODO)
    └── partner-6.png (TODO)
```

## Next Steps

1. Replace SVG logo with actual brand logo
2. Generate or source avatar images
3. Add team member professional photos
4. Include office location photography
5. Add partner company logos
6. Add hero background image (1920x1080px, optimized for web)

All paths are relative and will work with the frontend asset linking system.
