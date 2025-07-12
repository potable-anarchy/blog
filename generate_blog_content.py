#!/usr/bin/env python3
"""
Blog Content Generator using OpenAI API
Generates authentic blog post content to replace templated posts
"""

import os
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
import openai
from openai import OpenAI

class BlogContentGenerator:
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key"""
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
        # Use relative paths that work both locally and in GitHub Actions
        self.posts_dir = Path('./posts')
        self.generated_content = {}
        
    def extract_post_metadata(self, html_file: Path) -> Dict:
        """Extract title, date, and category from HTML file"""
        content = html_file.read_text()
        
        # Extract title
        title_match = re.search(r'<h1 class="post-title">(.*?)</h1>', content)
        title = title_match.group(1) if title_match else html_file.stem
        
        # Extract date
        date_match = re.search(r'<span class="post-date">(.*?)</span>', content)
        date = date_match.group(1) if date_match else "Unknown"
        
        # Extract category
        category_match = re.search(r'<span class="post-category">(.*?)</span>', content)
        category = category_match.group(1) if category_match else "Engineering"
        
        return {
            'filename': html_file.name,
            'title': title,
            'date': date,
            'category': category,
            'path': str(html_file)
        }
    
    def is_templated_post(self, html_file: Path) -> bool:
        """Check if post contains templated content"""
        content = html_file.read_text()
        
        # Look for specific template indicators (exact phrases from templated content)
        template_patterns = [
            "Sometimes the best engineering insights come from the most unexpected places",
            "Building reliable systems at scale requires both technical expertise and hard-won experience",
            "Leadership in technology requires balancing multiple competing priorities",
            "DevOps is where the rubber meets the road in software engineering",
            "Every challenge starts with understanding the problem space",
            "The solution required both technical precision and strategic thinking",
            "Looking ahead, I'm excited about how these lessons will apply to future challenges"
        ]
        
        # A post is templated if it contains multiple template patterns
        pattern_count = sum(1 for pattern in template_patterns if pattern in content)
        return pattern_count >= 2
    
    def get_templated_posts(self) -> List[Dict]:
        """Get all posts that still have templated content"""
        templated_posts = []
        
        for html_file in self.posts_dir.glob('*.html'):
            if self.is_templated_post(html_file):
                metadata = self.extract_post_metadata(html_file)
                templated_posts.append(metadata)
        
        return templated_posts
    
    def create_prompt_template(self, post_metadata: Dict) -> str:
        """Create a detailed prompt for generating authentic blog content"""
        
        # Base prompt with examples from successful posts
        base_prompt = f"""Write an authentic, personal blog post for a software engineer's blog called "Potable Anarchy". 

TITLE: {post_metadata['title']}
DATE: {post_metadata['date']}
CATEGORY: {post_metadata['category']}

REQUIREMENTS:
1. Start with a specific, real scenario or anecdote that connects to the title topic
2. Include concrete details, timestamps, specific technical terms, and personal experiences
3. Make genuine connections between the topic and engineering/technical concepts
4. Use a conversational, authentic tone with humor and personality
5. Include multiple sections with descriptive headings
6. Be substantial (1000+ words) with specific examples and anecdotes
7. Avoid generic templated language
8. End with a personal reflection or call to action

SUCCESSFUL EXAMPLES OF TONE AND STYLE:
- "At 2:47 AM, I'm awakened by screaming. Not from PagerDuty this time—from my 3-year-old..."
- "It's 3 AM and our payment processing system is down. Users are flooding our support channels..."
- "July 4th, 2023. I'm standing in my backyard at 8:47 PM, watching my neighbor set up what appears to be a small artillery battery of fireworks..."

The post should feel like it was written by someone with real experience, specific technical knowledge, and genuine insights. Include:
- Specific names, times, technical details
- Real-world parallels that aren't forced
- Personal anecdotes with concrete details
- Technical insights that come from actual experience
- A conversational, authentic voice

Write ONLY the content that would go inside the <div class="post-content"> tags. Do not include HTML tags, just the content paragraphs and headings.
"""
        
        # Add category-specific guidance
        if post_metadata['category'] in ['Incident Management', 'SRE']:
            base_prompt += "\n\nFOCUS: Connect this topic to incident response, system reliability, monitoring, or production operations with specific technical examples."
        elif post_metadata['category'] in ['Leadership', 'Team']:
            base_prompt += "\n\nFOCUS: Connect this topic to engineering leadership, team dynamics, or management with specific workplace scenarios."
        elif post_metadata['category'] in ['DevOps', 'Operations']:
            base_prompt += "\n\nFOCUS: Connect this topic to deployment, infrastructure, automation, or operations with specific technical examples."
        
        return base_prompt
    
    def generate_content(self, post_metadata: Dict, max_retries: int = 3) -> Optional[str]:
        """Generate content for a single post using OpenAI API"""
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please set OPENAI_API_KEY.")
            
        prompt = self.create_prompt_template(post_metadata)
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a skilled technical writer creating authentic, personal blog content for a software engineer. Write engaging, specific, and technically accurate content that feels genuinely personal."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.7
                )
                
                content = response.choices[0].message.content.strip()
                
                # Basic validation
                if len(content) < 500:
                    print(f"Generated content too short for {post_metadata['filename']}, retrying...")
                    continue
                    
                return content
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {post_metadata['filename']}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Failed to generate content for {post_metadata['filename']} after {max_retries} attempts")
                    return None
        
        return None
    
    def generate_all_content(self, posts: List[Dict], batch_size: int = 5) -> Dict[str, str]:
        """Generate content for all posts in batches"""
        results = {}
        
        for i in range(0, len(posts), batch_size):
            batch = posts[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(posts) + batch_size - 1)//batch_size}")
            
            for post in batch:
                print(f"Generating content for: {post['title']}")
                content = self.generate_content(post)
                
                if content:
                    results[post['filename']] = content
                    print(f"✓ Generated {len(content)} characters for {post['filename']}")
                else:
                    print(f"✗ Failed to generate content for {post['filename']}")
                
                # Rate limiting
                time.sleep(1)
            
            # Longer pause between batches
            if i + batch_size < len(posts):
                print("Pausing between batches...")
                time.sleep(5)
        
        return results
    
    def save_generated_content(self, content_dict: Dict[str, str], output_file: str = "generated_content.json"):
        """Save generated content to JSON file for review"""
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content_dict, f, indent=2, ensure_ascii=False)
        print(f"Generated content saved to {output_path}")
    
    def apply_content_to_post(self, filename: str, new_content: str) -> bool:
        """Apply generated content to a blog post HTML file"""
        html_file = self.posts_dir / filename
        
        if not html_file.exists():
            print(f"File not found: {html_file}")
            return False
        
        try:
            # Read current content
            current_content = html_file.read_text()
            
            # Find the content section and replace it
            content_pattern = r'(<div class="post-content">)(.*?)(</div>)'
            
            # Format the new content with proper HTML
            formatted_content = self.format_content_as_html(new_content)
            replacement = f'\\1\n{formatted_content}\n            \\3'
            
            # Replace the content
            updated_content = re.sub(content_pattern, replacement, current_content, flags=re.DOTALL)
            
            # Write back to file
            html_file.write_text(updated_content)
            print(f"✓ Updated {filename}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to update {filename}: {e}")
            return False
    
    def format_content_as_html(self, content: str) -> str:
        """Convert plain text content to HTML format"""
        lines = content.split('\n')
        html_lines = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            if not line:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                continue
            
            # Headers
            if line.startswith('## '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('# '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h1>{line[2:]}</h1>')
            # List items
            elif line.startswith('- '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'    <li>{line[2:]}</li>')
            # Regular paragraphs
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<p>{line}</p>')
        
        if in_list:
            html_lines.append('</ul>')
        
        # Add proper indentation
        return '                ' + '\n\n                '.join(html_lines)


def main():
    """Main execution function"""
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    generator = BlogContentGenerator(api_key)
    
    # Get all templated posts
    print("Scanning for templated posts...")
    templated_posts = generator.get_templated_posts()
    print(f"Found {len(templated_posts)} templated posts to process")
    
    if not templated_posts:
        print("No templated posts found!")
        return
    
    # Display posts to be processed
    print("\nPosts to be processed:")
    for post in templated_posts:
        print(f"  - {post['title']} ({post['date']})")
    
    # Auto-confirm in automated mode or ask for confirmation
    try:
        confirm = input(f"\nGenerate content for {len(templated_posts)} posts? (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
    except EOFError:
        # Auto-confirm if running in automated mode (no interactive input)
        print("Auto-confirming in automated mode...")
        confirm = 'y'
    
    # Generate all content
    print("\nGenerating content...")
    generated_content = generator.generate_all_content(templated_posts)
    
    # Save generated content
    generator.save_generated_content(generated_content)
    
    print(f"\nGeneration complete! Generated content for {len(generated_content)} posts.")
    
    # Apply content to files
    if generated_content:
        try:
            apply = input("Apply generated content to blog posts? (y/N): ")
        except EOFError:
            # Auto-confirm in automated mode
            print("Auto-confirming application in automated mode...")
            apply = 'y'
            
        if apply.lower() == 'y':
            print("\nApplying content to blog posts...")
            success_count = 0
            for filename, content in generated_content.items():
                if generator.apply_content_to_post(filename, content):
                    success_count += 1
            
            print(f"\nSuccessfully updated {success_count}/{len(generated_content)} posts")
        else:
            print("Generated content saved to generated_content.json for manual review")


if __name__ == "__main__":
    main()