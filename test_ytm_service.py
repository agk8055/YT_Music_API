#!/usr/bin/env python3
"""
Test the YTM service directly
"""

import asyncio
from services.ytm_service import YTMService

async def test_service():
    print("Testing YTM Service...")
    
    try:
        # Create service
        service = YTMService()
        
        if service.ytm is None:
            print("❌ YTM service is None")
            return False
        
        print("✅ YTM service created successfully")
        
        # Test search
        print("Testing search...")
        results = await service.search("test", limit=3)
        
        print(f"Results: {results}")
        
        if results and len(results) > 0:
            first_result = results[0]
            if "mock" in str(first_result).lower():
                print("❌ Still getting mock data")
                return False
            else:
                print("✅ Getting real data!")
                return True
        else:
            print("❌ No results returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_service())
    if success:
        print("\n🎉 YTM service is working with real data!")
    else:
        print("\n❌ YTM service is still using mock data") 