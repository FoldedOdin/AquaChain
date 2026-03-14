#!/usr/bin/env python3
"""Test with the JWT token from the browser."""

import requests

def test_with_token():
    url = "https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev/api/v1/readings/ESP32-001/latest"
    
    # Use the JWT token from your browser (truncated for security)
    token = "eyJraWQiOiJiWUJ3RGVsWVlkYmFIeVwvcUtlWXJPbDJlUVk2d1hIODVlM00zOFFBMEloWT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI1MWEzZWQ0YS1jMGIxLTcwZTgtYTdkNy0xOWQ3Y2EwMzVmZTAiLCJjb2duaXRvOmdyb3VwcyI6WyJjb25zdW1lcnMiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aC0xLmFtYXpvbmF3cy5jb21cL2FwLXNvdXRoLTFfUVVEbDdoRzh1IiwicGhvbmVfbnVtYmVyX3ZlcmlmaWVkIjpmYWxzZSwiY29nbml0bzp1c2VybmFtZSI6IjUxYTNlZDRhLWMwYjEtNzBlOC1hN2Q3LTE5ZDdjYTAzNWZlMCIsImdpdmVuX25hbWUiOiJLYXJ0aGlrIiwib3JpZ2luX2p0aSI6ImJlYWU1ZmFlLWJkNzEtNGJkNi1hNzE5LTNhNzE5ZjE5ZjE5ZiIsImF1ZCI6IjNkZGNhNzNhNzNhNzNhNzNhNzNhNzNhNzNhNzNhNzNhIiwiZXZlbnRfaWQiOiJiZWFlNWZhZS1iZDcxLTRiZDYtYTcxOS0zYTcxOWYxOWYxOWYiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTc3MzQ3NjM3OCwiaWF0IjoxNzczNDc2Mzc4LCJmYW1pbHlfbmFtZSI6IksgUHJhZGVlcCIsImp0aSI6Ijc5OTQ0Y2EwLWE1ZDItNDMxNi05NjFhLWI5M2IzYzBkMTkwNiIsImVtYWlsIjoia2FydGhpa2twcmFkZWVwMTIzQGdtYWlsLmNvbSJ9.iww0BVQZXGB8jA78XcloG6bK58cGb8V1G5sfLhAo8vJpH20DyAj14hSC6uNbpXnPbLw3SO0cYFk56f3p9KnAou3uKmB87tZ88vSTn2aj5pMf2sgSwTpXWZRg2IAnSR_FsIPku26zPJ_rpUptW2UR_Vlwcs0eCEOUqjiWg9eMQlx7znLhlcdoU4oFEeMQOLau4pA8i-aZ5eEI2tGpjr_I3hMzuP4U7naiT3TBO1LNzPqJU1Tzb4_HhYsM1s3aGNouFghAB5buaEdQt4BFaj-pfk0bveYupiOorm8E8xqRr1qPsKzG6z8mIFuZK4F5GfJZGD19DYLSjF-PjutNyl0WPA"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Origin': 'http://localhost:3000',
        'Content-Type': 'application/json'
    }
    
    print("🧪 Testing with auth token...")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        print("CORS Headers:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! The endpoint works with auth")
        else:
            print(f"❌ Still getting {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_with_token()