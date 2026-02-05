
import sys
import os
import requests
import json

# Configuration
API_URL = "http://localhost:6080/api"
AUTH_URL = "http://localhost:6081/api/system/login"  # Use employees app for auth as api doesn't have login yet

def get_token():
    """Get a valid JWT token from employees app"""
    payload = {"email": "system@pronto.com", "password": "pronto_system"}
    try:
        response = requests.post(AUTH_URL, json=payload)
        response.raise_for_status()
        # Check if token is in cookies or body
        token = response.cookies.get("access_token_cookie")
        if not token:
             # Fallback if returned in body (unlikely for browser-targeted auth but good for safety)
             data = response.json()
             token = data.get("access_token")
        
        if not token:
            print("❌ Failed to obtain token: No token in cookie or response")
            sys.exit(1)
            
        return token
    except Exception as e:
        print(f"❌ Failed to login: {e}")
        sys.exit(1)

def verify_endpoint(name, url, token):
    headers = {"Authorization": f"Bearer {token}"}
    # Also include cookie if that's how middleware expects it
    cookies = {"access_token_cookie": token}
    
    try:
        print(f"Testing {name} at {url}...")
        response = requests.get(url, headers=headers, cookies=cookies)
        
        if response.status_code == 200:
            data = response.json()
            # Basic validation
            if "status" in data and data["status"] == "success":
                 print(f"✅ {name}: OK ({len(data.get('data', {}).get(name, [])) if 'data' in data else 'valid response'})")
                 return True
            # Check for direct list response if format differs
            print(f"✅ {name}: OK (Status 200)")
            return True
        else:
            print(f"❌ {name}: Failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ {name}: Exception {e}")
        return False

def verify_create_cancel(url, token):
    """Test full order lifecycle: Create -> Cancel"""
    headers = {"Authorization": f"Bearer {token}"}
    cookies = {"access_token_cookie": token}
    
    print(f"Testing Order Lifecycle at {url}...")
    
    # 0. Get valid menu item
    item_id = 1
    try:
        menu_resp = requests.get(f"{url}/menu", headers=headers, cookies=cookies)
        if menu_resp.status_code == 200:
            menu_data = menu_resp.json()
            # Try to find an item. Structure might be categories -> items or flat list?
            # API /menu usually returns categories list, each with items.
            # Assuming standard structure: {"data": [{"items": [{"id": ...}]}]} or list
            data_content = menu_data.get("data", menu_data)
            found = False
            if isinstance(data_content, list):
                for cat in data_content:
                    items = cat.get("items", [])
                    if items:
                         item_id = items[0].get("id")
                         found = True
                         break
            if found:
                print(f"Using valid Menu Item ID: {item_id}")
            else:
                 print("⚠️ Could not extract valid item ID from menu, defaulting to 1")

    except Exception:
         print("⚠️ Failed to fetch menu for ID extraction")

    # 1. Create Order
    payload = {
        "customer": {"name": "Test User", "email": "test@pronto.com"},
        "items": [
             {"menu_item_id": item_id, "quantity": 1} 
        ],
        "table_number": "T1"
    }
    
    try:
        # Note: We might get validation error if item 1 doesn't exist, 
        # but we check for 201 Created or 400 with specific error to know endpoint is hit.
        resp = requests.post(f"{url}/orders", json=payload, headers=headers, cookies=cookies)
        
        if resp.status_code == 201:
            data = resp.json()
            # Extract order_id from response (either 'data' wrapper or direct)
            # API usually returns {status: success, data: {...}} or direct dict
            order_data = data.get("data", data)
            order_id = order_data.get("order_id") or order_data.get("id")
            session_id = order_data.get("session_id")
            
            print(f"✅ Order Created: ID {order_id} (Session {session_id})")
            
            if not order_id or not session_id:
                print("❌ Failed to parse order/session ID")
                return False
                
            # 2. Cancel Order
            cancel_payload = {"reason": "Verification Test", "session_id": session_id}
            cancel_resp = requests.post(f"{url}/orders/{order_id}/cancel", json=cancel_payload, headers=headers, cookies=cookies)
            
            if cancel_resp.status_code == 200:
                 print(f"✅ Order {order_id} Cancelled")
                 return True
            else:
                 print(f"❌ Cancel Failed: {cancel_resp.status_code} - {cancel_resp.text}")
                 return False

        elif resp.status_code == 400:
             # If bad request (e.g. invalid item), we at least know endpoint is reachable
             print(f"⚠️ Order Create reachable but rejected (likely data): {resp.text}")
             # We count reachable as partial success for structural verification? 
             # No, strictly better to conform.
             return False
        else:
             print(f"❌ Order Create Failed: {resp.status_code} - {resp.text}")
             return False
             
    except Exception as e:
        print(f"❌ Exception in Cycle: {e}")
        return False

def main():
    print("Getting authentication token...")
    token = get_token()
    print("Token obtained.")
    
    results = []
    results.append(verify_endpoint("orders", f"{API_URL}/orders", token))
    results.append(verify_endpoint("promotions", f"{API_URL}/promotions", token))
    results.append(verify_endpoint("menu", f"{API_URL}/menu", token))
    results.append(verify_create_cancel(API_URL, token))
    
    if all(results):
        print("\n✨ All endpoints verified successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Some validation checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
