#!/usr/bin/env python3
"""
Setup script for Gemini API integration

This script helps configure the Gemini API key for enhanced explanations.
"""

import os
import sys
from pathlib import Path

def setup_gemini_api():
    """Setup Gemini API key for the demo."""
    
    print("🤖 Nyayamrit Gemini API Setup")
    print("=" * 40)
    
    # Check if already configured
    current_key = os.getenv("GEMINI_API_KEY")
    if current_key:
        print(f"✅ Gemini API key already configured: {current_key[:10]}...")
        choice = input("Do you want to update it? (y/N): ").lower()
        if choice != 'y':
            return
    
    print("\nTo enable enhanced explanations with Gemini AI:")
    print("1. Go to https://makersuite.google.com/app/apikey")
    print("2. Create a new API key")
    print("3. Copy the API key")
    print()
    
    api_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("⚠️  Skipping Gemini setup. Basic responses will be used.")
        return
    
    # Set environment variable for current session
    os.environ["GEMINI_API_KEY"] = api_key
    
    # Try to create/update .env file
    env_file = Path(__file__).parent / "web_interface" / ".env"
    
    try:
        # Read existing .env file
        env_content = ""
        if env_file.exists():
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # Remove existing GEMINI_API_KEY lines
            lines = [line for line in lines if not line.startswith("GEMINI_API_KEY=")]
            env_content = "".join(lines)
        
        # Add new API key
        env_content += f"GEMINI_API_KEY={api_key}\n"
        
        # Write back to .env file
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Gemini API key saved to {env_file}")
        
    except Exception as e:
        print(f"⚠️  Could not save to .env file: {e}")
        print("You can manually set the environment variable:")
        print(f"export GEMINI_API_KEY={api_key}")
    
    # Test the API key
    print("\n🧪 Testing Gemini API connection...")
    
    try:
        # Try to import and test Gemini
        sys.path.append(str(Path(__file__).parent))
        from llm_integration.providers import GeminiProvider
        
        gemini = GeminiProvider(api_key=api_key)
        
        if gemini.is_available():
            print("✅ Gemini API connection successful!")
            print("🚀 Enhanced explanations will be available in the demo.")
        else:
            print("❌ Gemini API connection failed.")
            print("Please check your API key and try again.")
            
    except ImportError as e:
        print(f"⚠️  Gemini library not installed: {e}")
        print("Install with: pip install google-generativeai")
        
    except Exception as e:
        print(f"❌ Error testing Gemini API: {e}")
    
    print("\n🎯 Setup complete!")
    print("Start the demo server with: python web_interface/simple_demo.py")

if __name__ == "__main__":
    setup_gemini_api()