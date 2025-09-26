from langchain_core.tools import tool
from typing import Annotated

# ===== SHARED HANDOFF TOOLS =====
@tool
def transfer_to_flight_specialist(
    reason: Annotated[str, "Why transferring to flight specialist"],
    user_request: Annotated[str, "What user wants with flights"]
) -> str:
    """Transfer current conversation to flight booking specialist"""
    return f"TRANSFER_TO_FLIGHT: {reason} | Request: {user_request}"

@tool
def transfer_to_hotel_specialist(
    reason: Annotated[str, "Why transferring to hotel specialist"],
    user_request: Annotated[str, "What user wants with hotels"]
) -> str:
    """Transfer current conversation to hotel booking specialist"""
    return f"TRANSFER_TO_HOTEL: {reason} | Request: {user_request}"

@tool
def transfer_to_general_assistant(
    reason: Annotated[str, "Why transferring to general assistant"],
    user_request: Annotated[str, "What user needs help with"]
) -> str:
    """Transfer conversation to general travel assistant"""
    return f"TRANSFER_TO_GENERAL: {reason} | Request: {user_request}"

# ===== WORK TOOLS =====
@tool
def search_flights(
    origin: Annotated[str, "Departure city"],
    destination: Annotated[str, "Arrival city"],
    date: Annotated[str, "Travel date"]
) -> str:
    """Search for available flights"""
    return f"Found flights from {origin} to {destination} on {date}"

@tool
def search_hotels(
    city: Annotated[str, "City to search hotels"],
    checkin: Annotated[str, "Check-in date"],
    checkout: Annotated[str, "Check-out date"]
) -> str:
    """Search for available hotels"""
    return f"Found hotels in {city} for {checkin} to {checkout}"

@tool
def book_flight(
    flight_id: Annotated[str, "Flight ID to book"],
    passenger_info: Annotated[str, "Passenger information"]
) -> str:
    """Book a specific flight"""
    return f"Flight {flight_id} booked for {passenger_info}"

@tool
def book_hotel(
    hotel_id: Annotated[str, "Hotel ID to book"],
    guest_info: Annotated[str, "Guest information"]
) -> str:
    """Book a specific hotel"""
    return f"Hotel {hotel_id} booked for {guest_info}"

@tool
def get_travel_info(
    destination: Annotated[str, "Travel destination"],
    info_type: Annotated[str, "Type of information needed"]
) -> str:
    """Get general travel information"""
    return f"Travel info for {destination}: {info_type}"

# ===== TOOL COLLECTIONS FOR EACH AGENT =====
FLIGHT_TOOLS = [
    search_flights,
    book_flight,
    transfer_to_hotel_specialist,
    transfer_to_general_assistant
]

HOTEL_TOOLS = [
    search_hotels,
    book_hotel,
    transfer_to_flight_specialist,
    transfer_to_general_assistant
]

GENERAL_TOOLS = [
    get_travel_info,
    transfer_to_flight_specialist,
    transfer_to_hotel_specialist
]
