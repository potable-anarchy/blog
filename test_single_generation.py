#!/usr/bin/env python3
"""
Test single post generation to verify the system works
"""

import os
from generate_blog_content import BlogContentGenerator

def main():
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    generator = BlogContentGenerator(api_key)
    
    # Test with just one post
    test_post = {
        'filename': 'spooky-automation-when-scripts-go-wrong.html',
        'title': 'Spooky Automation: When Scripts Go Wrong', 
        'date': 'October 19, 2024',
        'category': 'DevOps'
    }
    
    print(f"Testing content generation for: {test_post['title']}")
    
    content = generator.generate_content(test_post)
    
    if content:
        print(f"✓ Generated {len(content)} characters")
        print("\nFirst 500 characters:")
        print(content[:500] + "...")
        
        # Save to test file
        with open('test_generated_content.txt', 'w') as f:
            f.write(content)
        print("\nFull content saved to test_generated_content.txt")
        
        # Test applying to HTML
        print("\nTesting HTML application...")
        success = generator.apply_content_to_post(test_post['filename'], content)
        if success:
            print("✓ Successfully applied content to HTML file")
        else:
            print("✗ Failed to apply content to HTML file")
    else:
        print("✗ Failed to generate content")

if __name__ == "__main__":
    main()