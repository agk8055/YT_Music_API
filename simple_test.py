#!/usr/bin/env python3
"""
Simple test to debug ytmusicapi search
"""

from ytmusicapi import YTMusic

def test_search():
    print("Testing YTM search directly...")
    
    try:
        ytm = YTMusic()
        print("✅ YTM initialized")
        
        # Test 1: Basic search
        print("Test 1: Basic search")
        results = ytm.search("test", limit=1)
        print(f"✅ Basic search: {len(results)} results")
        
        # Test 2: Search with filter
        print("Test 2: Search with filter")
        results = ytm.search("leo", limit=1, filter="songs")
        print(f"✅ Filtered search: {len(results)} results")
        
        if results:
            print(f"First result: {results[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_search()
    if success:
        print("\n🎉 Search is working!")
    else:
        print("\n❌ Search failed") 