# File: app/data/models.py

"""
Data models for Neo Cafe
"""
from datetime import datetime
import time
import uuid
from app.utils.auth_utils import hash_password

class User:
    """User model"""
    
    def __init__(self, username, email, password=None, role="customer", **kwargs):
        """
        Initialize User
        
        Args:
            username (str): Username
            email (str): Email address
            password (str, optional): Password
            role (str, optional): User role (admin, staff, customer)
            **kwargs: Additional user attributes
        """
        self.id = kwargs.get("id", str(uuid.uuid4()))
        self.username = username
        self.email = email
        self.password_hash = hash_password(password) if password else kwargs.get("password_hash")
        self.role = role
        self.first_name = kwargs.get("first_name", "")
        self.last_name = kwargs.get("last_name", "")
        self.phone = kwargs.get("phone", "")
        self.created_at = kwargs.get("created_at", datetime.now().isoformat())
        self.updated_at = kwargs.get("updated_at")
        self.last_login = kwargs.get("last_login")
    
    def to_dict(self):
        """
        Convert to dictionary
        
        Returns:
            dict: User data
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create User from dictionary
        
        Args:
            data (dict): User data
            
        Returns:
            User: User instance
        """
        return cls(
            username=data.get("username"),
            email=data.get("email"),
            role=data.get("role", "customer"),
            **{k: v for k, v in data.items() if k not in ["username", "email", "role"]}
        )

class MenuItem:
    """Menu item model"""
    
    def __init__(self, name, price, description, category, **kwargs):
        """
        Initialize MenuItem
        
        Args:
            name (str): Item name
            price (float): Item price
            description (str): Item description
            category (str): Item category
            **kwargs: Additional item attributes
        """
        self.id = kwargs.get("id", int(time.time()))
        self.name = name
        self.price = price
        self.description = description
        self.category = category
        self.image = kwargs.get("image")
        self.popular = kwargs.get("popular", False)
        self.vegetarian = kwargs.get("vegetarian", False)
        self.vegan = kwargs.get("vegan", False)
        self.gluten_free = kwargs.get("gluten_free", False)
        self.available = kwargs.get("available", True)
        self.nutritional_info = kwargs.get("nutritional_info")
        self.special_features = kwargs.get("special_features")
    
    def to_dict(self):
        """
        Convert to dictionary
        
        Returns:
            dict: Item data
        """
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "category": self.category,
            "image": self.image,
            "popular": self.popular,
            "vegetarian": self.vegetarian,
            "vegan": self.vegan,
            "gluten_free": self.gluten_free,
            "available": self.available,
            "nutritional_info": self.nutritional_info,
            "special_features": self.special_features
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create MenuItem from dictionary
        
        Args:
            data (dict): Item data
            
        Returns:
            MenuItem: MenuItem instance
        """
        return cls(
            name=data.get("name"),
            price=data.get("price"),
            description=data.get("description"),
            category=data.get("category"),
            **{k: v for k, v in data.items() if k not in ["name", "price", "description", "category"]}
        )

class Order:
    """Order model"""
    
    def __init__(self, items, username, **kwargs):
        """
        Initialize Order
        
        Args:
            items (list): Order items
            username (str): Customer username
            **kwargs: Additional order attributes
        """
        self.id = kwargs.get("id", f"ORD-{int(time.time())}")
        self.items = items
        self.username = username
        self.total = kwargs.get("total", sum(item.get("price", 0) * item.get("quantity", 1) for item in items))
        self.status = kwargs.get("status", "New")
        self.special_instructions = kwargs.get("special_instructions")
        self.delivery_location = kwargs.get("delivery_location", "Table 1")
        self.payment_method = kwargs.get("payment_method", "Credit Card")
        self.created_at = kwargs.get("created_at", datetime.now().isoformat())
        self.updated_at = kwargs.get("updated_at")
        self.completed_at = kwargs.get("completed_at")
    
    def to_dict(self):
        """
        Convert to dictionary
        
        Returns:
            dict: Order data
        """
        return {
            "id": self.id,
            "items": self.items,
            "username": self.username,
            "total": self.total,
            "status": self.status,
            "special_instructions": self.special_instructions,
            "delivery_location": self.delivery_location,
            "payment_method": self.payment_method,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create Order from dictionary
        
        Args:
            data (dict): Order data
            
        Returns:
            Order: Order instance
        """
        return cls(
            items=data.get("items", []),
            username=data.get("username"),
            **{k: v for k, v in data.items() if k not in ["items", "username"]}
        )

class Delivery:
    """Delivery model"""
    
    def __init__(self, order_id, robot_id, destination, **kwargs):
        """
        Initialize Delivery
        
        Args:
            order_id (str): Order ID
            robot_id (str): Robot ID
            destination (dict): Destination coordinates
            **kwargs: Additional delivery attributes
        """
        self.id = kwargs.get("id", f"DEL-{int(time.time())}")
        self.order_id = order_id
        self.robot_id = robot_id
        self.destination = destination
        self.status = kwargs.get("status", "preparing")
        self.progress = kwargs.get("progress", 0)
        self.estimated_delivery_time = kwargs.get("estimated_delivery_time", "15 minutes")
        self.route = kwargs.get("route", [])
        self.created_at = kwargs.get("created_at", datetime.now().isoformat())
        self.updated_at = kwargs.get("updated_at")
        self.completed_at = kwargs.get("completed_at")
    
    def to_dict(self):
        """
        Convert to dictionary
        
        Returns:
            dict: Delivery data
        """
        return {
            "id": self.id,
            "order_id": self.order_id,
            "robot_id": self.robot_id,
            "destination": self.destination,
            "status": self.status,
            "progress": self.progress,
            "estimated_delivery_time": self.estimated_delivery_time,
            "route": self.route,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create Delivery from dictionary
        
        Args:
            data (dict): Delivery data
            
        Returns:
            Delivery: Delivery instance
        """
        return cls(
            order_id=data.get("order_id"),
            robot_id=data.get("robot_id"),
            destination=data.get("destination"),
            **{k: v for k, v in data.items() if k not in ["order_id", "robot_id", "destination"]}
        )