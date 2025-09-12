# import os
# import re
# import shutil

# # Paths (using raw strings to handle Windows backslashes correctly)
# posts_dir = r"E:\MahinBlogs\content\BlogPosts"
# attachments_dir = r"E:\MahinObs\attachments"
# static_images_dir = r"E:\MahinBlogs\static\images"

# # Step 1: Process each markdown file in the posts directory
# for filename in os.listdir(posts_dir):
#     if filename.endswith(".md"):
#         filepath = os.path.join(posts_dir, filename)
        
#         with open(filepath, "r", encoding="utf-8") as file:
#             content = file.read()
        
#         # Step 2: Find all image links in the format ![Image Description](/images/Pasted%20image%20...%20.png)
#         images = re.findall(r'\[\[([^]]*\.png)\]\]', content)
        
#         # Step 3: Replace image links and ensure URLs are correctly formatted
#         for image in images:
#             # Prepare the Markdown-compatible link with %20 replacing spaces
#             markdown_image = f"![Image Description](/images/{image.replace(' ', '%20')})"
#             content = content.replace(f"[[{image}]]", markdown_image)
            
#             # Step 4: Copy the image to the Hugo static/images directory if it exists
#             image_source = os.path.join(attachments_dir, image)
#             if os.path.exists(image_source):
#                 shutil.copy(image_source, static_images_dir)

#         # Step 5: Write the updated content back to the markdown file
#         with open(filepath, "w", encoding="utf-8") as file:
#             file.write(content)

# print("Markdown files processed and images copied successfully.")

import os
import re
import shutil
import urllib.parse

# === Paths ===
posts_dir = r"E:\MahinBlogs\content"            # scan all content recursively
attachments_dir = r"E:\MahinObs\attachments"     # your Obsidian attachments root
static_images_dir = r"E:\MahinBlogs\static\images"

# Make sure destination exists
os.makedirs(static_images_dir, exist_ok=True)

# Build an index of every image under attachments_dir: {lower_filename: [full_paths]}
image_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
index = {}
for root, _, files in os.walk(attachments_dir):
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in image_exts:
            key = f.lower()
            index.setdefault(key, []).append(os.path.join(root, f))

# Regex to match Obsidian wikilinks that refer to image files.
# - optional leading '!' for embeds
# - capture the path/filename up to extension
# - allow optional '|...' after filename (size/alias), which we ignore
pat = re.compile(
    r'!?\[\[([^\]\|]+\.(?:png|jpg|jpeg|gif|webp|svg))(?:\|[^\]]*)?\]\]',
    re.IGNORECASE
)

changed_files = 0
copied = 0
missing = []

def replace_one(m):
    """Convert one wikilink to Markdown image link and schedule copy."""
    target = m.group(1)  # e.g., 'Pasted image.png' or 'attachments/foo.jpg'
    base = os.path.basename(target)  # filename only
    key = base.lower()

    # Find the source file
    src_path = None
    # First try direct join if target included a subfolder that lives under attachments_dir
    direct_candidate = os.path.join(attachments_dir, target)
    if os.path.exists(direct_candidate):
        src_path = direct_candidate
    else:
        # Fall back to lookup by filename anywhere under attachments_dir
        matches = index.get(key, [])
        if matches:
            src_path = matches[0]  # take the first match
    if not src_path:
        missing.append(target)
        # Keep the original text unchanged if we didn't find the file
        return m.group(0)

    # Copy to static/images if not already there
    dest_path = os.path.join(static_images_dir, base)
    if not os.path.exists(dest_path):
        shutil.copy2(src_path, dest_path)
        global copied
        copied += 1

    # Build Markdown image link with URL-encoded filename
    alt = os.path.splitext(base)[0]
    url_name = urllib.parse.quote(base)
    return f"![{alt}](images/{url_name})"

# Walk all markdown files under posts_dir
for root, _, files in os.walk(posts_dir):
    for fname in files:
        if fname.lower().endswith((".md", ".markdown")):
            path = os.path.join(root, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            new_content = pat.sub(replace_one, content)

            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                changed_files += 1

print(f"Updated {changed_files} markdown files.")
print(f"Copied {copied} image(s) to {static_images_dir}.")
if missing:
    print("Images referenced but not found under attachments:")
    for m in sorted(set(missing)):
        print("  -", m)
