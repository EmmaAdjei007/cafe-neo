# File: chainlit_app/states.py

"""
State management classes for Neo Cafe chatbot
"""
import time
import requests
from datetime import datetime
import os
import uuid
from typing import List, Dict, Optional, Any

# Import voice processing libraries if available
try:
    import speech_recognition as sr
    speech_recognition_available = True
except ImportError:
    speech_recognition_available = False
    print("Speech recognition not available. Install with 'pip install SpeechRecognition'")

try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    tts_available = True
except ImportError:
    tts_available = False
    print("Text-to-speech not available. Install with 'pip install pyttsx3'")

# Constants
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:8050')
ROBOT_SIMULATOR_URL = os.environ.get('ROBOT_SIMULATOR_URL', 'http://localhost:8051')


class VoiceState:
    """
    Manages voice processing state
    """
    def __init__(self):
        self.voice_enabled = False
        self.recognizer = None
        
        # Initialize speech recognition if available
        if speech_recognition_available:
            self.recognizer = sr.Recognizer()
            self.voice_enabled = True
    
    def toggle_voice(self):
        """Toggle voice mode on/off"""
        self.voice_enabled = not self.voice_enabled
        return self.voice_enabled
    
    def is_enabled(self):
        """Check if voice mode is enabled"""
        return self.voice_enabled and speech_recognition_available
    
    def recognize_speech(self):
        """
        Recognize speech from microphone
        
        Returns:
            str: Recognized text or error message
        """
        if not self.is_enabled():
            return "Voice recognition is not enabled or available"
        
        try:
            with sr.Microphone() as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                # Try to recognize using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                return f"Recognized: {text}"
            
        except sr.WaitTimeoutError:
            return "Listening timed out. Please try again."
        except sr.UnknownValueError:
            return "Could not understand audio. Please try again."
        except sr.RequestError as e:
            return f"Could not request results; {e}"
        except Exception as e:
            return f"Error recognizing speech: {e}"
    
    def speak_text(self, text):
        """
        Convert text to speech
        
        Args:
            text (str): Text to speak
            
        Returns:
            bool: Success or failure
        """
        if not self.is_enabled() or not tts_available:
            return False
        
        try:
            # Start in a separate thread to avoid blocking
            import threading
            threading.Thread(target=self._speak, args=(text,), daemon=True).start()
            return True
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return False
    
    def _speak(self, text):
        """Internal function to speak text"""
        tts_engine.say(text)
        tts_engine.runAndWait()


class OrderState:
    """
    Manages order state
    """
    def __init__(self):
        self.items = []
        self.total_price = 0.0
        self.special_instructions = None
        self.order_confirmed = False
        self.order_id = None
        self.delivery_location = "Table 1"  # Default location
        self.payment_method = "Credit Card"  # Default payment method
    
    def add_item(self, item_name, quantity=1):
        """Add item to order"""
        # Import needed here to avoid circular imports
        from chainlit_app.app import menu_items
        
        # Find the item in the menu
        menu_item = next((item for item in menu_items if item["name"].lower() == item_name.lower()), None)
        if not menu_item:
            return f"Sorry, {item_name} is not on our menu."
        
        # Check if item already in order
        existing_item = next((i for i in self.items if i["name"].lower() == item_name.lower()), None)
        if existing_item:
            # Update quantity
            existing_item["quantity"] += quantity
        else:
            # Add new item
            self.items.append({
                "name": menu_item["name"],
                "price": menu_item.get("price", 0),
                "quantity": quantity
            })
        
        # Update total price
        self.total_price = sum(item["price"] * item["quantity"] for item in self.items)
        
        return f"Added {quantity}x {menu_item['name']} to your order."
    
    def remove_item(self, item_name):
        """Remove item from order"""
        # Find the item in the order
        item_index = next((i for i, item in enumerate(self.items) if item["name"].lower() == item_name.lower()), None)
        if item_index is None:
            return f"Sorry, {item_name} is not in your order."
        
        # Remove the item
        removed_item = self.items.pop(item_index)
        
        # Update total price
        self.total_price = sum(item["price"] * item["quantity"] for item in self.items)
        
        return f"Removed {removed_item['name']} from your order."
    
    def clear_order(self):
        """Clear the order"""
        self.items = []
        self.total_price = 0.0
        self.special_instructions = None
        self.order_confirmed = False
        self.order_id = None
        
        return "Your order has been cleared."
    
    def set_delivery_location(self, location):
        """Set delivery location"""
        self.delivery_location = location
        return f"Delivery location set to {location}."
    
    def set_payment_method(self, method):
        """Set payment method"""
        valid_methods = ["Cash", "Credit Card", "Mobile Payment"]
        if method not in valid_methods:
            return f"Sorry, {method} is not a valid payment method. Valid options are: {', '.join(valid_methods)}."
        
        self.payment_method = method
        return f"Payment method set to {method}."
    
    def add_special_instructions(self, instructions):
        """Add special instructions"""
        self.special_instructions = instructions
        return "Special instructions added to your order."
    
    def confirm_order(self):
        """Confirm the order"""
        if not self.items:
            return "Your order is empty. Please add items before confirming."
        
        # Generate order ID
        timestamp = int(time.time())
        self.order_id = f"ORD-{timestamp}"
        self.order_confirmed = True
        
        # Try to send order to main app
        try:
            order_data = self.get_order_data()
            
            response = requests.post(
                f"{DASHBOARD_URL}/api/place-order",
                json=order_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"Order {self.order_id} sent to dashboard successfully")
            else:
                print(f"Failed to send order to dashboard: {response.status_code}")
                
        except Exception as e:
            print(f"Error sending order to dashboard: {e}")
        
        # Return confirmation message
        return f"Thank you for your order! Your order ID is {self.order_id}. Your total is ${self.total_price:.2f}."
    
    def get_order_data(self):
        """Get order data as a dictionary for API calls"""
        return {
            "id": self.order_id or f"TEMP-{uuid.uuid4().hex[:8]}",
            "items": self.items,
            "total": self.total_price,
            "special_instructions": self.special_instructions,
            "delivery_location": self.delivery_location,
            "payment_method": self.payment_method,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "confirmed" if self.order_confirmed else "draft"
        }
    
    def get_order_summary(self):
        """Get order summary"""
        if not self.items:
            return "Your order is empty."
        
        # Build summary
        summary = "**Your Order:**\n\n"
        for item in self.items:
            summary += f"- {item['quantity']}x {item['name']} (${item['price'] * item['quantity']:.2f})\n"
        
        if self.special_instructions:
            summary += f"\n**Special Instructions:** {self.special_instructions}\n"
        
        summary += f"\n**Delivery Location:** {self.delivery_location}\n"
        summary += f"**Payment Method:** {self.payment_method}\n"
        summary += f"**Total:** ${self.total_price:.2f}"
        
        if self.order_confirmed:
            summary += f"\n\n**Status:** Confirmed ✅ (Order ID: {self.order_id})"
        
        return summary


class RobotState:
    """
    Manages robot state for delivery service
    """
    def __init__(self):
        self.active_deliveries = {}
        self.status = "idle"  # idle, busy, maintenance
        self.battery_level = 100
        self.location = {"lat": 0, "lng": 0}
    
    def get_status(self, order_id=None):
        """
        Get robot status for an order or general status
        
        Args:
            order_id (str, optional): Order ID
            
        Returns:
            dict: Robot status
        """
        # Try to get status from robot simulator
        try:
            if order_id:
                response = requests.get(
                    f"{ROBOT_SIMULATOR_URL}/api/delivery/{order_id}",
                    timeout=3
                )
                
                if response.status_code == 200:
                    return response.json()
            
            # Get general robot status
            response = requests.get(
                f"{ROBOT_SIMULATOR_URL}/api/status",
                timeout=3
            )
            
            if response.status_code == 200:
                robot_data = response.json()
                # Update local state
                self.status = robot_data.get("status", self.status)
                self.battery_level = robot_data.get("battery_level", self.battery_level)
                self.location = robot_data.get("location", self.location)
                return robot_data
        
        except Exception as e:
            print(f"Error getting robot status: {e}")
        
        # Return local state if request failed
        if order_id and order_id in self.active_deliveries:
            return self.active_deliveries[order_id]
        
        return {
            "status": self.status,
            "battery_level": self.battery_level,
            "location": self.location,
            "active_deliveries": len(self.active_deliveries)
        }
    
    def format_status_message(self, order_id=None):
        """
        Format robot status message
        
        Args:
            order_id (str, optional): Order ID
            
        Returns:
            str: Formatted status message
        """
        status_data = self.get_status(order_id)
        
        if order_id:
            # Order-specific status
            if not status_data or "status" not in status_data:
                return "No information available for this order."
            
            status = status_data.get("status", "unknown")
            eta = status_data.get("estimated_delivery_time", "unknown")
            progress = status_data.get("progress", 0)
            message = status_data.get("message", "")
            
            # Format status message
            status_message = f"**Order Status: {status.title()}**\n\n"
            status_message += f"{message}\n\n"
            
            if status != "delivered":
                status_message += f"**ETA:** {eta}\n"
                status_message += f"**Progress:** {progress:.0f}%\n"
            
            return status_message
        else:
            # General robot status
            status_message = f"**Robot Status: {status_data.get('status', 'Unknown').title()}**\n\n"
            status_message += f"**Battery Level:** {status_data.get('battery_level', 0)}%\n"
            status_message += f"**Active Deliveries:** {status_data.get('active_deliveries', 0)}\n"
            
            if status_data.get("status") == "busy":
                status_message += "\nRobot is currently delivering orders."
            elif status_data.get("status") == "maintenance":
                status_message += "\nRobot is currently undergoing maintenance."
            else:
                status_message += "\nRobot is ready for new deliveries."
            
            return status_message