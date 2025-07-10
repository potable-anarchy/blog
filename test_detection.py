#!/usr/bin/env python3
"""
Test script to detect templated posts without requiring API key
"""

from generate_blog_content import BlogContentGenerator

def main():
    generator = BlogContentGenerator()
    
    # Get all templated posts
    print("Scanning for templated posts...")
    templated_posts = generator.get_templated_posts()
    print(f"Found {len(templated_posts)} templated posts to process")
    
    if templated_posts:
        print("\nTemplated posts found:")
        for i, post in enumerate(templated_posts, 1):
            print(f"{i:2d}. {post['title']} ({post['date']}) [{post['category']}]")
    else:
        print("No templated posts found!")

if __name__ == "__main__":
    main()