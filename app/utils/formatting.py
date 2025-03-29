# File: app/utils/formatting.py

"""
Formatting utilities for Neo Cafe
"""
from datetime import datetime
import re

def format_currency(amount, currency="$"):
    """
    Format a number as currency
    
    Args:
        amount (float): Amount to format
        currency (str): Currency symbol
        
    Returns:
        str: Formatted currency string
    """
    try:
        return f"{currency}{float(amount):.2f}"
    except (ValueError, TypeError):
        return f"{currency}0.00"

def format_percentage(value, decimal_places=2):
    """
    Format a number as percentage
    
    Args:
        value (float): Value to format (0-1)
        decimal_places (int): Number of decimal places
        
    Returns:
        str: Formatted percentage string
    """
    try:
        value = float(value)
        
        # If value is in decimal form (0-1), convert to percentage
        if 0 <= value <= 1:
            value *= 100
        
        return f"{value:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return "0.00%"

def format_date(date_string, input_format=None, output_format="%b %d, %Y"):
    """
    Format a date string
    
    Args:
        date_string (str): Date string to format
        input_format (str, optional): Input date format
        output_format (str): Output date format
        
    Returns:
        str: Formatted date string
    """
    try:
        # Try to parse as ISO format first
        if input_format is None:
            try:
                date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                # Try to guess format
                date_formats = [
                    "%Y-%m-%d",
                    "%Y/%m/%d",
                    "%m/%d/%Y",
                    "%d/%m/%Y",
                    "%b %d, %Y",
                    "%d %b %Y"
                ]
                
                for fmt in date_formats:
                    try:
                        date_obj = datetime.strptime(date_string, fmt)
                        break
                    except (ValueError, TypeError):
                        continue
                else:
                    # No format matched
                    return date_string
        else:
            # Use provided input format
            date_obj = datetime.strptime(date_string, input_format)
        
        # Format the date
        return date_obj.strftime(output_format)
    except (ValueError, TypeError, AttributeError):
        return date_string

def format_time(time_string, input_format=None, output_format="%I:%M %p"):
    """
    Format a time string
    
    Args:
        time_string (str): Time string to format
        input_format (str, optional): Input time format
        output_format (str): Output time format
        
    Returns:
        str: Formatted time string
    """
    try:
        # Try to parse as ISO format first
        if input_format is None:
            try:
                if 'T' in time_string:
                    # ISO datetime string
                    time_obj = datetime.fromisoformat(time_string.replace('Z', '+00:00'))
                else:
                    # Try common time formats
                    time_formats = [
                        "%H:%M",
                        "%H:%M:%S",
                        "%I:%M %p",
                        "%I:%M:%S %p"
                    ]
                    
                    for fmt in time_formats:
                        try:
                            time_obj = datetime.strptime(time_string, fmt)
                            break
                        except (ValueError, TypeError):
                            continue
                    else:
                        # No format matched
                        return time_string
            except (ValueError, AttributeError):
                return time_string
        else:
            # Use provided input format
            time_obj = datetime.strptime(time_string, input_format)
        
        # Format the time
        return time_obj.strftime(output_format)
    except (ValueError, TypeError, AttributeError):
        return time_string

def format_datetime(datetime_string, input_format=None, output_format="%b %d, %Y %I:%M %p"):
    """
    Format a datetime string
    
    Args:
        datetime_string (str): Datetime string to format
        input_format (str, optional): Input datetime format
        output_format (str): Output datetime format
        
    Returns:
        str: Formatted datetime string
    """
    try:
        # Try to parse as ISO format first
        if input_format is None:
            try:
                datetime_obj = datetime.fromisoformat(datetime_string.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                # Try to guess format
                datetime_formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y/%m/%d %H:%M:%S",
                    "%m/%d/%Y %I:%M %p",
                    "%d/%m/%Y %H:%M"
                ]
                
                for fmt in datetime_formats:
                    try:
                        datetime_obj = datetime.strptime(datetime_string, fmt)
                        break
                    except (ValueError, TypeError):
                        continue
                else:
                    # No format matched
                    return datetime_string
        else:
            # Use provided input format
            datetime_obj = datetime.strptime(datetime_string, input_format)
        
        # Format the datetime
        return datetime_obj.strftime(output_format)
    except (ValueError, TypeError, AttributeError):
        return datetime_string

def format_phone(phone_number):
    """
    Format a phone number
    
    Args:
        phone_number (str): Phone number to format
        
    Returns:
        str: Formatted phone number
    """
    try:
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone_number)
        
        # Format based on length
        if len(digits) == 10:
            # US format: (123) 456-7890
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            # US format with country code: 1 (123) 456-7890
            return f"1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            # Return original with some formatting
            if len(digits) >= 7:
                return f"{digits[:-7]}-{digits[-7:-4]}-{digits[-4:]}"
            else:
                return phone_number
    except (TypeError, AttributeError):
        return phone_number

def truncate_text(text, max_length=100, suffix="..."):
    """
    Truncate text to a maximum length
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        suffix (str): Suffix to add when truncated
        
    Returns:
        str: Truncated text
    """
    try:
        if len(text) <= max_length:
            return text
        
        # Truncate at word boundary
        truncated = text[:max_length].rsplit(' ', 1)[0]
        return truncated + suffix
    except (TypeError, AttributeError):
        return text

def format_list(items, conjunction="and", oxford_comma=True):
    """
    Format a list as a string
    
    Args:
        items (list): List of items
        conjunction (str): Conjunction for last item
        oxford_comma (bool): Whether to use Oxford comma
        
    Returns:
        str: Formatted list string
    """
    if not items:
        return ""
    
    if len(items) == 1:
        return str(items[0])
    
    if len(items) == 2:
        return f"{items[0]} {conjunction} {items[1]}"
    
    # More than 2 items
    if oxford_comma:
        return f"{', '.join(str(item) for item in items[:-1])}, {conjunction} {items[-1]}"
    else:
        return f"{', '.join(str(item) for item in items[:-1])} {conjunction} {items[-1]}"

def format_file_size(size_bytes):
    """
    Format file size from bytes to human-readable format
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted file size
    """
    try:
        size_bytes = float(size_bytes)
        
        # Define size units
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        
        # Calculate appropriate unit
        unit_index = 0
        while size_bytes >= 1024 and unit_index < len(units) - 1:
            size_bytes /= 1024
            unit_index += 1
        
        # Format with appropriate precision
        if unit_index == 0:
            # Bytes: no decimal places
            return f"{int(size_bytes)} {units[unit_index]}"
        else:
            # KB and above: up to 2 decimal places
            return f"{size_bytes:.2f} {units[unit_index]}".rstrip('0').rstrip('.') + f" {units[unit_index]}"
    except (ValueError, TypeError):
        return "0 B"

def format_duration(seconds):
    """
    Format duration in seconds to human-readable format
    
    Args:
        seconds (int/float): Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    try:
        seconds = float(seconds)
        
        # Convert to reasonable units
        if seconds < 60:
            # Less than a minute
            return f"{int(seconds)} seconds"
        
        minutes = seconds / 60
        if minutes < 60:
            # Less than an hour
            return f"{int(minutes)} minute{'s' if minutes != 1 else ''}"
        
        hours = minutes / 60
        if hours < 24:
            # Less than a day
            hours_int = int(hours)
            minutes_int = int(minutes % 60)
            
            if minutes_int == 0:
                return f"{hours_int} hour{'s' if hours_int != 1 else ''}"
            else:
                return f"{hours_int} hour{'s' if hours_int != 1 else ''} {minutes_int} minute{'s' if minutes_int != 1 else ''}"
        
        days = hours / 24
        if days < 7:
            # Less than a week
            days_int = int(days)
            hours_int = int(hours % 24)
            
            if hours_int == 0:
                return f"{days_int} day{'s' if days_int != 1 else ''}"
            else:
                return f"{days_int} day{'s' if days_int != 1 else ''} {hours_int} hour{'s' if hours_int != 1 else ''}"
        
        weeks = days / 7
        if weeks < 4:
            # Less than a month
            weeks_int = int(weeks)
            days_int = int(days % 7)
            
            if days_int == 0:
                return f"{weeks_int} week{'s' if weeks_int != 1 else ''}"
            else:
                return f"{weeks_int} week{'s' if weeks_int != 1 else ''} {days_int} day{'s' if days_int != 1 else ''}"
        
        months = days / 30.44  # Average month length
        if months < 12:
            # Less than a year
            months_int = int(months)
            days_int = int(days % 30.44)
            
            if days_int == 0:
                return f"{months_int} month{'s' if months_int != 1 else ''}"
            else:
                return f"{months_int} month{'s' if months_int != 1 else ''} {days_int} day{'s' if days_int != 1 else ''}"
        
        years = days / 365.25  # Account for leap years
        years_int = int(years)
        months_int = int((days % 365.25) / 30.44)
        
        if months_int == 0:
            return f"{years_int} year{'s' if years_int != 1 else ''}"
        else:
            return f"{years_int} year{'s' if years_int != 1 else ''} {months_int} month{'s' if months_int != 1 else ''}"
    
    except (ValueError, TypeError):
        return "0 seconds"

def format_relative_time(timestamp):
    """
    Format a timestamp as relative time (e.g., "5 minutes ago")
    
    Args:
        timestamp (str/datetime): Timestamp to format
        
    Returns:
        str: Relative time string
    """
    try:
        # Convert string to datetime if needed
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                # Try common formats
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                    "%m/%d/%Y %H:%M:%S",
                    "%m/%d/%Y"
                ]
                
                for fmt in formats:
                    try:
                        timestamp = datetime.strptime(timestamp, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return timestamp
        
        # Get current time
        now = datetime.now()
        
        # Compute time difference
        diff = now - timestamp
        
        # Convert to seconds
        diff_seconds = diff.total_seconds()
        
        # Format based on difference
        if diff_seconds < 0:
            # Future time
            return "in the future"
        
        if diff_seconds < 60:
            # Less than a minute
            return "just now"
        
        if diff_seconds < 3600:
            # Less than an hour
            minutes = int(diff_seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        
        if diff_seconds < 86400:
            # Less than a day
            hours = int(diff_seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        
        if diff_seconds < 604800:
            # Less than a week
            days = int(diff_seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        
        if diff_seconds < 2592000:
            # Less than a month
            weeks = int(diff_seconds / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        
        if diff_seconds < 31536000:
            # Less than a year
            months = int(diff_seconds / 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"
        
        # More than a year
        years = int(diff_seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"
    
    except (ValueError, TypeError, AttributeError):
        return str(timestamp)

def slugify(text):
    """
    Convert text to URL-friendly slug
    
    Args:
        text (str): Text to convert
        
    Returns:
        str: Slugified text
    """
    try:
        # Convert to lowercase
        text = text.lower()
        
        # Replace non-alphanumeric characters with hyphens
        text = re.sub(r'[^a-z0-9]+', '-', text)
        
        # Remove leading/trailing hyphens
        text = text.strip('-')
        
        # Collapse multiple hyphens
        text = re.sub(r'-+', '-', text)
        
        return text
    except (AttributeError, TypeError):
        return ""

def format_card_number(card_number):
    """
    Format a credit card number with masking
    
    Args:
        card_number (str): Card number to format
        
    Returns:
        str: Formatted card number
    """
    try:
        # Remove non-digit characters
        digits = re.sub(r'\D', '', card_number)
        
        # Mask all but last 4 digits
        masked = '*' * (len(digits) - 4) + digits[-4:]
        
        # Group into blocks of 4
        formatted = ' '.join([masked[i:i+4] for i in range(0, len(masked), 4)])
        
        return formatted
    except (AttributeError, TypeError):
        return ""

def format_address(address_parts):
    """
    Format address parts into a formatted address string
    
    Args:
        address_parts (dict): Dictionary of address parts
            (street, city, state, zip, country)
        
    Returns:
        str: Formatted address
    """
    try:
        lines = []
        
        # Add street
        if address_parts.get('street'):
            lines.append(address_parts['street'])
        
        # Add city, state zip
        city_state_zip = []
        if address_parts.get('city'):
            city_state_zip.append(address_parts['city'])
        
        if address_parts.get('state'):
            city_state_zip.append(address_parts['state'])
        
        if address_parts.get('zip'):
            city_state_zip.append(address_parts['zip'])
        
        if city_state_zip:
            lines.append(', '.join(city_state_zip))
        
        # Add country
        if address_parts.get('country'):
            lines.append(address_parts['country'])
        
        # Join lines with newlines
        return '\n'.join(lines)
    except (AttributeError, TypeError):
        return ""

def sanitize_html(html_string):
    """
    Sanitize HTML string to remove potentially dangerous tags
    
    Args:
        html_string (str): HTML string to sanitize
        
    Returns:
        str: Sanitized HTML string
    """
    try:
        # Remove script tags
        sanitized = re.sub(r'<script.*?>.*?</script>', '', html_string, flags=re.DOTALL)
        
        # Remove style tags
        sanitized = re.sub(r'<style.*?>.*?</style>', '', sanitized, flags=re.DOTALL)
        
        # Remove iframe tags
        sanitized = re.sub(r'<iframe.*?>.*?</iframe>', '', sanitized, flags=re.DOTALL)
        
        # Remove event handlers
        sanitized = re.sub(r' on\w+=".*?"', '', sanitized)
        
        # Remove javascript: URLs
        sanitized = re.sub(r'javascript:', 'disabled-javascript:', sanitized)
        
        return sanitized
    except (TypeError, AttributeError):
        return ""