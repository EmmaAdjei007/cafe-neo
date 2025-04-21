#!/usr/bin/env python
"""
Simple test script to verify token encoding/decoding
"""
import base64
import json
import sys

def encode_token(data):
    """Encode data as base64 token"""
    if isinstance(data, str):
        # Parse JSON string
        try:
            data = json.loads(data)
        except:
            data = {"username": data}
    
    # Convert to JSON and encode
    json_data = json.dumps(data)
    token = base64.b64encode(json_data.encode()).decode()
    return token

def decode_token(token):
    """Decode token back to data"""
    try:
        # Handle potential padding issues
        missing_padding = len(token) % 4
        if missing_padding:
            token += '=' * (4 - missing_padding)
            
        decoded = base64.b64decode(token)
        data = json.loads(decoded)
        return data
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

if __name__ == "__main__":
    # Simple test
    if len(sys.argv) < 2:
        print("Usage: python test_token.py 'username' OR python test_token.py '{\"username\":\"test\",\"role\":\"admin\"}'")
        sys.exit(1)
    
    input_data = sys.argv[1]
    
    # Encode
    token = encode_token(input_data)
    print(f"Input: {input_data}")
    print(f"Encoded token: {token}")
    
    # Decode
    decoded = decode_token(token)
    print(f"Decoded data: {decoded}")
    
    if decoded and isinstance(decoded, dict) and 'username' in decoded:
        print(f"✅ Success! Token properly encodes and decodes username: {decoded['username']}")
    else:
        print("❌ Error: Could not properly encode/decode the token")