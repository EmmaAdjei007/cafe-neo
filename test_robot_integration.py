#!/usr/bin/env python3
# File: test_robot_integration.py
# A simple test script to verify the robot delivery integration

import requests
import json
import time
import argparse
import sys
from pathlib import Path
import threading

# Default API URL - replace with your robot API URL
DEFAULT_API_URL = "http://172.29.104.124:8001/api"

# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description='Test Neo Cafe robot delivery integration')
    parser.add_argument('--url', default=DEFAULT_API_URL, help='Robot API URL')
    parser.add_argument('--interface', default='en7', help='Network interface')
    parser.add_argument('--test', default='all', choices=['start', 'status', 'cancel', 'all'], 
                       help='Test to run')
    parser.add_argument('--order-id', default=None, help='Order ID to use for testing')
    parser.add_argument('--location', default='123 Main St, Apt 4B', 
                       help='Delivery location for testing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    return parser.parse_args()

# Test starting a robot delivery
def test_start_delivery(api_url, interface_name, order_id, location, verbose=False):
    print(f"\n[TEST] Starting robot delivery")
    
    # Generate order ID if not provided
    if not order_id:
        order_id = f"TEST-ORDER-{int(time.time())}"
    
    # Prepare the payload
    payload = {
        "interface_name": interface_name,
        "order_id": order_id,
        "delivery_location": location
    }
    
    if verbose:
        print(f"Request URL: {api_url}/delivery/start")
        print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make the API call
        response = requests.post(
            f"{api_url}/delivery/start",
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=10
        )
        
        # Check response
        if response.status_code in (200, 201, 202):
            print(f"✅ SUCCESS: Robot delivery started")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return order_id, True
        else:
            print(f"❌ ERROR: Failed to start robot delivery")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return order_id, False
    
    except Exception as e:
        print(f"❌ ERROR: Exception while starting delivery: {str(e)}")
        return order_id, False

# Test getting delivery status
def test_delivery_status(api_url, order_id, verbose=False):
    print(f"\n[TEST] Getting robot delivery status")
    
    if verbose:
        print(f"Request URL: {api_url}/delivery/status?order_id={order_id}")
    
    try:
        # Make the API call
        response = requests.get(
            f"{api_url}/delivery/status",
            params={"order_id": order_id},
            timeout=5
        )
        
        # Check response
        if response.status_code == 200:
            print(f"✅ SUCCESS: Got delivery status")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ ERROR: Failed to get delivery status")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ ERROR: Exception while getting status: {str(e)}")
        return False

# Test canceling a delivery
def test_cancel_delivery(api_url, order_id, verbose=False):
    print(f"\n[TEST] Canceling robot delivery")
    
    # Prepare the payload
    payload = {
        "order_id": order_id
    }
    
    if verbose:
        print(f"Request URL: {api_url}/delivery/cancel")
        print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make the API call
        response = requests.post(
            f"{api_url}/delivery/cancel",
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=5
        )
        
        # Check response
        if response.status_code == 200:
            print(f"✅ SUCCESS: Robot delivery cancelled")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ ERROR: Failed to cancel robot delivery")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ ERROR: Exception while canceling delivery: {str(e)}")
        return False

# Simulate robot movement (for testing)
def simulate_robot_movement(api_url, order_id, verbose=False):
    print(f"\n[INFO] Simulating robot movement for order {order_id}")
    
    # Starting coordinates (Neo Cafe location)
    lat, lng = 37.7749, -122.4194
    
    # Define waypoints for the robot path (incrementing coordinates)
    waypoints = [
        {"lat": lat + 0.001 * i, "lng": lng + 0.001 * i} 
        for i in range(1, 6)
    ]
    
    # Send location updates for each waypoint
    for i, location in enumerate(waypoints):
        # Prepare the payload
        payload = {
            "order_id": order_id,
            "robot_location": location,
            "status": "in_transit",
            "battery_level": 90 - i * 3,  # Simulate battery drain
            "connection_quality": max(60, 90 - i * 5),  # Simulate connection fluctuation
            "eta": f"{5 - i} minutes"
        }
        
        if verbose:
            print(f"Simulated location update {i+1}/{len(waypoints)}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            # Make the API call to update location
            response = requests.post(
                f"{api_url}/delivery/update",
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ Location update {i+1} sent successfully")
            else:
                print(f"⚠️ Location update failed: {response.status_code}")
        
        except Exception as e:
            print(f"⚠️ Error sending location update: {str(e)}")
        
        # Wait before sending next update
        time.sleep(2)
    
    # Final update - delivered
    final_payload = {
        "order_id": order_id,
        "robot_location": waypoints[-1],
        "status": "delivered",
        "battery_level": 75,
        "connection_quality": 85,
        "eta": "Delivered"
    }
    
    try:
        response = requests.post(
            f"{api_url}/delivery/update",
            headers={'Content-Type': 'application/json'},
            json=final_payload,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ Final delivery update sent successfully")
        else:
            print(f"⚠️ Final delivery update failed: {response.status_code}")
    
    except Exception as e:
        print(f"⚠️ Error sending final update: {str(e)}")

def run_tests(args):
    """Run the selected tests"""
    order_id = args.order_id
    
    # Run tests based on selection
    if args.test == 'all' or args.test == 'start':
        order_id, success = test_start_delivery(
            args.url, args.interface, order_id, args.location, args.verbose
        )
        
        if success and (args.test == 'all'):
            # Start a thread to simulate robot movement
            if args.verbose:
                print("[INFO] Starting robot movement simulation")
            
            movement_thread = threading.Thread(
                target=simulate_robot_movement,
                args=(args.url, order_id, args.verbose)
            )
            movement_thread.daemon = True
            movement_thread.start()
            
            # Give the movement thread a moment to start
            time.sleep(1)
    
    if args.test == 'all' or args.test == 'status':
        if not order_id:
            print("❌ ERROR: Order ID required for status test")
        else:
            test_delivery_status(args.url, order_id, args.verbose)
    
    if args.test == 'all' or args.test == 'cancel':
        if not order_id:
            print("❌ ERROR: Order ID required for cancel test")
        else:
            # For 'all' test, wait a bit to allow status check and some movement before canceling
            if args.test == 'all':
                time.sleep(5)
            
            test_cancel_delivery(args.url, order_id, args.verbose)
    
    print("\n[SUMMARY]")
    print(f"API URL: {args.url}")
    print(f"Tests run: {args.test}")
    if order_id:
        print(f"Order ID: {order_id}")
    print("Tests completed!")

if __name__ == "__main__":
    args = parse_args()
    run_tests(args)