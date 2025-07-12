#!/usr/bin/env python3
"""
Build script to generate index.html with blog posts sorted by date
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

class BlogIndexBuilder:
    def __init__(self):
        # Use relative paths that work both locally and in GitHub Actions
        self.posts_dir = Path('./posts')
        self.index_file = Path('./index.html')
        self.posts = []
        
    def extract_post_info(self, html_file: Path) -> Dict:
        """Extract metadata from a blog post HTML file"""
        content = html_file.read_text()
        
        # Extract title
        title_match = re.search(r'<h1 class="post-title">(.*?)</h1>', content)
        title = title_match.group(1) if title_match else html_file.stem.replace('-', ' ').title()
        
        # Extract date
        date_match = re.search(r'<span class="post-date">(.*?)</span>', content)
        date_str = date_match.group(1) if date_match else "Unknown"
        
        # Parse date for sorting
        try:
            date_obj = datetime.strptime(date_str, "%B %d, %Y")
        except:
            try:
                date_obj = datetime.strptime(date_str, "%B %Y")
            except:
                date_obj = datetime.min
        
        # Extract category
        category_match = re.search(r'<span class="post-category">(.*?)</span>', content)
        category = category_match.group(1) if category_match else "Engineering"
        
        # Extract first paragraph for excerpt
        excerpt_match = re.search(r'<div class="post-content">\s*<p>(.*?)</p>', content, re.DOTALL)
        if excerpt_match:
            excerpt = excerpt_match.group(1).strip()
            # Clean up the excerpt
            excerpt = re.sub(r'<[^>]+>', '', excerpt)  # Remove HTML tags
            excerpt = excerpt.replace('\n', ' ')
            # Truncate to reasonable length
            if len(excerpt) > 150:
                excerpt = excerpt[:147] + "..."
        else:
            excerpt = f"Insights on {category.lower()} and engineering..."
        
        return {
            'filename': html_file.name,
            'title': title,
            'date': date_str,
            'date_obj': date_obj,
            'category': category,
            'excerpt': excerpt,
            'path': f'posts/{html_file.name}'
        }
    
    def get_category_icon(self, category: str) -> Tuple[str, str]:
        """Get icon and background class for category"""
        category_map = {
            'SRE': ('🔧📊', 'tech-bg'),
            'DevOps': ('🚀🔨', 'diy-bg'),
            'Leadership': ('👥📈', 'nature-bg'),
            'Personal': ('🎵📅', 'music-bg'),
            'Incident Management': ('🚨🔥', 'aviation-bg'),
            'Team': ('👥🤝', 'nature-bg'),
            'Engineering': ('⚙️💻', 'tech-bg')
        }
        return category_map.get(category, ('📝💭', 'tech-bg'))
    
    def generate_post_card(self, post: Dict) -> str:
        """Generate HTML for a single post card"""
        icon, bg_class = self.get_category_icon(post['category'])
        
        return f'''                        <article class="post-card">
                            <div class="post-image">
                                <div class="placeholder-image {bg_class}" role="img" aria-label="{post['title']}">
                                    <span>{icon}</span>
                                </div>
                            </div>
                            <div class="post-content">
                                <div class="post-meta">
                                    <span class="post-date">{post['date']}</span>
                                    <span class="post-category">{post['category']}</span>
                                </div>
                                <h3 class="post-title">{post['title']}</h3>
                                <p class="post-excerpt">{post['excerpt']}</p>
                                <a href="{post['path']}" class="read-more">Read More</a>
                            </div>
                        </article>'''
    
    def load_all_posts(self):
        """Load metadata from all blog posts"""
        for html_file in self.posts_dir.glob('*.html'):
            post_info = self.extract_post_info(html_file)
            self.posts.append(post_info)
        
        # Sort by date (newest first)
        self.posts.sort(key=lambda x: x['date_obj'], reverse=True)
        print(f"Loaded {len(self.posts)} posts")
    
    def build_index(self):
        """Build the index.html file with sorted posts"""
        # Read the current index.html
        current_content = self.index_file.read_text()
        
        # Find the blog posts section
        start_marker = '<!-- AUTO-GENERATED POSTS START -->'
        end_marker = '<!-- AUTO-GENERATED POSTS END -->'
        
        start_pos = current_content.find(start_marker)
        end_pos = current_content.find(end_marker)
        
        if start_pos == -1 or end_pos == -1:
            print("Error: Could not find blog posts section markers in index.html")
            return False
        
        # Generate new posts HTML
        posts_html = '\n'.join(self.generate_post_card(post) for post in self.posts)
        
        # Build new content
        new_content = (
            current_content[:start_pos + len(start_marker)] + 
            '\n' + posts_html + '\n                    ' +
            current_content[end_pos:]
        )
        
        # Write the updated index
        self.index_file.write_text(new_content)
        print(f"Updated index.html with {len(self.posts)} posts sorted by date")
        return True
    
    def print_post_summary(self):
        """Print summary of posts by date"""
        print("\nPosts by date (newest first):")
        for i, post in enumerate(self.posts[:10], 1):
            print(f"{i:2d}. {post['date']} - {post['title']}")
        if len(self.posts) > 10:
            print(f"    ... and {len(self.posts) - 10} more posts")


def main():
    """Main execution function"""
    builder = BlogIndexBuilder()
    
    print("Building blog index...")
    builder.load_all_posts()
    builder.print_post_summary()
    
    if builder.build_index():
        print("\n✓ Index built successfully!")
        print("Run this script whenever you add new posts to keep them sorted by date.")
    else:
        print("\n✗ Failed to build index")


if __name__ == "__main__":
    main()