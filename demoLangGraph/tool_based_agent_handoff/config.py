"""
Configuration for Tool-based Agent Handoff System
"""

# Agent Configuration
AGENT_CONFIG = {
    "flight_specialist": {
        "name": "Flight Specialist",
        "emoji": "✈️",
        "description": "Chuyên viên vé máy bay",
        "work_tools": ["search_flights", "book_flight"],
        "handoff_tools": ["transfer_to_hotel_specialist", "transfer_to_general_assistant"],
        "keywords": ["vé", "máy bay", "flight", "bay", "đặt vé"]
    },
    "hotel_specialist": {
        "name": "Hotel Specialist", 
        "emoji": "🏨",
        "description": "Chuyên viên khách sạn",
        "work_tools": ["search_hotels", "book_hotel"],
        "handoff_tools": ["transfer_to_flight_specialist", "transfer_to_general_assistant"],
        "keywords": ["khách sạn", "hotel", "phòng", "nghỉ", "đặt phòng"]
    },
    "general_assistant": {
        "name": "General Assistant",
        "emoji": "💬", 
        "description": "Trợ lý du lịch tổng quát",
        "work_tools": ["get_travel_info"],
        "handoff_tools": ["transfer_to_flight_specialist", "transfer_to_hotel_specialist"],
        "keywords": ["tư vấn", "thông tin", "du lịch", "hướng dẫn"]
    }
}

# Tool Configuration
TOOL_CONFIG = {
    "handoff_tools": {
        "transfer_to_flight_specialist": {
            "description": "Chuyển giao đến chuyên viên vé máy bay",
            "parameters": ["reason", "user_request"]
        },
        "transfer_to_hotel_specialist": {
            "description": "Chuyển giao đến chuyên viên khách sạn", 
            "parameters": ["reason", "user_request"]
        },
        "transfer_to_general_assistant": {
            "description": "Chuyển giao đến trợ lý tổng quát",
            "parameters": ["reason", "user_request"]
        }
    },
    "work_tools": {
        "search_flights": {
            "description": "Tìm kiếm vé máy bay",
            "parameters": ["origin", "destination", "date"]
        },
        "search_hotels": {
            "description": "Tìm kiếm khách sạn",
            "parameters": ["city", "checkin", "checkout"]
        },
        "book_flight": {
            "description": "Đặt vé máy bay",
            "parameters": ["flight_id", "passenger_info"]
        },
        "book_hotel": {
            "description": "Đặt khách sạn",
            "parameters": ["hotel_id", "guest_info"]
        },
        "get_travel_info": {
            "description": "Lấy thông tin du lịch",
            "parameters": ["destination", "info_type"]
        }
    }
}

# Routing Configuration
ROUTING_CONFIG = {
    "transfer_patterns": [
        "TRANSFER_TO_FLIGHT:",
        "TRANSFER_TO_HOTEL:", 
        "TRANSFER_TO_GENERAL:"
    ],
    "end_signals": [
        "cảm ơn", "tạm biệt", "bye", "kết thúc", "xong", "đủ rồi"
    ],
    "default_agent": "general_assistant"
}

# System Configuration
SYSTEM_CONFIG = {
    "max_conversation_turns": 10,
    "memory_ttl": 300,  # 5 minutes
    "default_mode": "true",  # true, simple, advanced
    "enable_stm": True,  # Short-term memory
    "debug_mode": False
}

# Prompt Templates
PROMPT_TEMPLATES = {
    "flight_specialist": """Bạn là chuyên viên vé máy bay. Bạn có thể:

1. XỬ LÝ flight requests: search_flights, book_flight
2. CHUYỂN GIAO khi cần:
   - transfer_to_hotel_specialist: nếu user cần hotel  
   - transfer_to_general_assistant: nếu câu hỏi không về flight

Ví dụ:
- "Tìm vé HCM-HN" → Dùng search_flights
- "Vé xong rồi, giờ tìm khách sạn" → transfer_to_hotel_specialist  
- "Thời tiết Hà Nội thế nào?" → transfer_to_general_assistant""",

    "hotel_specialist": """Bạn là chuyên viên khách sạn. Bạn có thể:

1. XỬ LÝ hotel requests: search_hotels, book_hotel
2. CHUYỂN GIAO khi cần:
   - transfer_to_flight_specialist: nếu user cần flight
   - transfer_to_general_assistant: nếu câu hỏi không về hotel""",

    "general_assistant": """Bạn là trợ lý du lịch tổng quát. Bạn:

1. TRẢ LỜI câu hỏi chung về du lịch, thời tiết, tư vấn
2. CHUYỂN GIAO đến specialist:
   - transfer_to_flight_specialist: khi user cần vé máy bay
   - transfer_to_hotel_specialist: khi user cần khách sạn"""
}

# Response Templates
RESPONSE_TEMPLATES = {
    "flight_specialist": "✈️ Flight Specialist: {message}",
    "hotel_specialist": "🏨 Hotel Specialist: {message}",
    "general_assistant": "💬 General Assistant: {message}"
}

# Error Messages
ERROR_MESSAGES = {
    "import_error": "❌ Import error: {error}",
    "agent_creation_error": "❌ Agent creation error: {error}",
    "tool_error": "❌ Tool error: {error}",
    "state_error": "❌ State error: {error}",
    "routing_error": "❌ Routing error: {error}",
    "llm_error": "❌ LLM error: {error}",
    "memory_error": "❌ Memory error: {error}"
}

# Success Messages  
SUCCESS_MESSAGES = {
    "import_success": "✅ All imports successful",
    "agent_creation_success": "✅ Agent created: {agent_name}",
    "tool_success": "✅ Tool result: {result}",
    "state_success": "✅ State created: {session_id}",
    "routing_success": "✅ Routing result: {result}",
    "conversation_success": "✅ Conversation completed!"
}
