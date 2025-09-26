from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import Tool
try:
    from .state import AgentState, normalize_messages
    from .state_manager import StateManager
    from .tools import FLIGHT_TOOLS, HOTEL_TOOLS, GENERAL_TOOLS
except ImportError:
    from state import AgentState, normalize_messages
    from state_manager import StateManager
    from tools import FLIGHT_TOOLS, HOTEL_TOOLS, GENERAL_TOOLS
from typing import List, Dict, Any


def _get_last_user_text(messages: List) -> str:
    """Return content of the most recent HumanMessage; fallback to last message text."""
    for msg in reversed(messages):
        # LangChain types or duck-typing
        if isinstance(msg, HumanMessage) or getattr(msg, "type", None) == "human":
            return getattr(msg, "content", "") or ""
    # Fallback: last message (may be AIMessage). Try best effort.
    last = messages[-1]
    return getattr(last, "content", str(last))


class BaseAgent:
    """Base class for all agents"""

    def __init__(self, llm, agent_name: str, tools: List[Tool]):
        self.llm = llm
        self.agent_name = agent_name
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}

    def _get_system_prompt(self) -> str:
        """Override in subclasses"""
        return "You are a helpful assistant."

    def _process_with_llm(self, messages: List, system_prompt: str) -> str:
        """Process messages with LLM and tools
        (Demo đơn giản; bản production hãy dùng LangChain Agent + tools thực)"""
        return f"[{self.agent_name}] Processing with LLM..."

    def process(self, state: AgentState) -> AgentState:
        """Main processing method with state management"""
        messages = normalize_messages(state.get("messages", []))

        if not messages:
            response = AIMessage(content=f"Hello! I'm the {self.agent_name}. How can I help you?")
            new_state = {**state, "messages": [response], "current_agent": self.agent_name}
        else:
            # Get context from previous agents
            context = StateManager.get_agent_context(self.agent_name, state)
            user_text = _get_last_user_text(messages)

            # Process with LLM and tools, including context
            system_prompt = self._get_system_prompt_with_context(context)
            llm_response = self._process_with_llm_and_context(messages, system_prompt, context, user_text)

            response = AIMessage(content=llm_response)
            messages.append(response)
            
            # Update state with collected data
            new_state = self._update_state_with_data(state, user_text, context)
            new_state["messages"] = messages
            new_state["current_agent"] = self.agent_name

        return new_state

    def _get_system_prompt_with_context(self, context: Dict[str, Any]) -> str:
        """Get system prompt with context from other agents"""
        base_prompt = self._get_system_prompt()
        
        # Add context from previous agents
        if context.get("previous_agents"):
            previous_agents = ", ".join(context["previous_agents"])
            base_prompt += f"\n\nContext from previous agents ({previous_agents}):"
            
            for agent, data in context.get("collected_data", {}).items():
                if data:
                    base_prompt += f"\n- {agent}: {data}"
        
        return base_prompt

    def _process_with_llm_and_context(self, messages: List, system_prompt: str, context: Dict[str, Any], user_text: str) -> str:
        """Process with LLM including context from other agents"""
        # This is a simplified version - in production, use actual LLM with tools
        return f"[{self.agent_name}] Processing with context: {context.get('conversation_phase', 'collecting')}\n\nCONVERSATION_COMPLETE: Processing completed"

    def _update_state_with_data(self, state: AgentState, user_text: str, context: Dict[str, Any]) -> AgentState:
        """Update state with data collected by this agent"""
        # Extract relevant data from user input and context
        collected_data = self._extract_data_from_input(user_text, context)
        
        # Update state with collected data
        new_state = StateManager.update_agent_data(self.agent_name, collected_data, state)
        
        # Mark agent as completed if task is done
        if self._is_task_completed(collected_data, context):
            new_state = StateManager.mark_agent_completed(self.agent_name, new_state)
        
        return new_state

    def _extract_data_from_input(self, user_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant data from user input - override in subclasses"""
        return {"user_input": user_text, "timestamp": "now"}

    def _is_task_completed(self, collected_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if agent's task is completed - override in subclasses"""
        return False


class FlightSpecialistAgent(BaseAgent):
    """Flight agent that can handle flights OR transfer to other agents"""

    def __init__(self, llm):
        super().__init__(llm, "flight_specialist", FLIGHT_TOOLS)

    def _get_system_prompt(self) -> str:
        return """Bạn là chuyên viên vé máy bay. Bạn có thể:

1. XỬ LÝ flight requests: search_flights, book_flight
2. CHUYỂN GIAO khi cần:
   - transfer_to_hotel_specialist: nếu user cần hotel
   - transfer_to_general_assistant: nếu câu hỏi không về flight

Ví dụ:
- "Tìm vé HCM-HN" → Dùng search_flights
- "Vé xong rồi, giờ tìm khách sạn" → transfer_to_hotel_specialist
- "Thời tiết Hà Nội thế nào?" → transfer_to_general_assistant"""

    def _process_with_llm_and_context(self, messages: List, system_prompt: str, context: Dict[str, Any], user_text: str) -> str:
        """Process flight-related requests with context"""
        user_text_lower = user_text.lower()

        flight_kw = ['vé', 'máy bay', 'flight', 'bay', 'chuyến bay', 'đặt vé']
        hotel_kw  = ['khách sạn', 'hotel', 'phòng', 'nghỉ', 'resort']

        # Check if we have flight info from previous agents
        flight_info = context.get("flight_info", {})
        hotel_info = context.get("hotel_info", {})

        # 1) Flight domain -> xử lý/ hỏi thêm, KHÔNG handoff
        if any(k in user_text_lower for k in flight_kw):
            if 'tìm' in user_text_lower or 'search' in user_text_lower:
                if flight_info:
                    return f"✈️ Flight Specialist: Dựa trên thông tin đã có {flight_info}, tôi đang tìm vé cho bạn. Cần thêm thông tin gì không?\n\nCONVERSATION_COMPLETE: Flight search completed"
                return "✈️ Flight Specialist: Tôi đang tìm vé cho bạn. Cho mình điểm đi/đến và ngày bay cụ thể nhé.\n\nCONVERSATION_COMPLETE: Waiting for flight details"
            return "✈️ Flight Specialist: Tôi có thể giúp bạn tìm/đặt vé. Bạn cần đi đâu và khi nào?\n\nCONVERSATION_COMPLETE: Waiting for flight request"

        # 2) Handoff sang Hotel khi cần
        if any(k in user_text_lower for k in hotel_kw):
            return "TRANSFER_TO_HOTEL: User asked for hotel from flight flow"

        # 3) Còn lại -> handoff về General
        return "TRANSFER_TO_GENERAL: General/non-flight question"

    def _extract_data_from_input(self, user_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract flight-related data from user input"""
        data = {"user_input": user_text, "timestamp": "now"}
        
        # Extract flight information
        if any(kw in user_text.lower() for kw in ['vé', 'máy bay', 'flight', 'bay']):
            data["flight_request"] = True
            data["raw_input"] = user_text
            
            # Simple extraction (in production, use NER)
            if 'hcm' in user_text.lower() or 'hồ chí minh' in user_text.lower():
                data["origin"] = "HCM"
            if 'hn' in user_text.lower() or 'hà nội' in user_text.lower():
                data["destination"] = "HN"
        
        return data

    def _is_task_completed(self, collected_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if flight task is completed"""
        return collected_data.get("flight_request", False) and "origin" in collected_data and "destination" in collected_data


class HotelSpecialistAgent(BaseAgent):
    """Hotel agent that can handle hotels OR transfer to other agents"""

    def __init__(self, llm):
        super().__init__(llm, "hotel_specialist", HOTEL_TOOLS)

    def _get_system_prompt(self) -> str:
        return """Bạn là chuyên viên khách sạn. Bạn có thể:

1. XỬ LÝ hotel requests: search_hotels, book_hotel
2. CHUYỂN GIAO khi cần:
   - transfer_to_flight_specialist: nếu user cần flight
   - transfer_to_general_assistant: nếu câu hỏi không về hotel"""

    def _process_with_llm_and_context(self, messages: List, system_prompt: str, context: Dict[str, Any], user_text: str) -> str:
        """Process hotel-related requests with context"""
        user_text_lower = user_text.lower()

        hotel_kw  = ['khách sạn', 'hotel', 'phòng', 'nghỉ', 'resort', 'đặt phòng']
        flight_kw = ['vé', 'máy bay', 'flight', 'bay', 'chuyến bay', 'đặt vé']

        # Check if we have hotel info from previous agents
        hotel_info = context.get("hotel_info", {})
        flight_info = context.get("flight_info", {})

        # 1) Hotel domain -> tư vấn/ hỏi thêm, KHÔNG handoff
        if any(k in user_text_lower for k in hotel_kw):
            if any(w in user_text_lower for w in ['tìm', 'search', 'gợi ý', 'tư vấn']):
                if hotel_info:
                    return f"🏨 Hotel Specialist: Dựa trên thông tin đã có {hotel_info}, tôi đang tìm khách sạn cho bạn. Cần thêm thông tin gì không?\n\nCONVERSATION_COMPLETE: Hotel search completed"
                return "🏨 Hotel Specialist: Mình có thể gợi ý khách sạn. Bạn muốn ở thành phố nào và ngày check-in/check-out?\n\nCONVERSATION_COMPLETE: Waiting for hotel details"
            # ví dụ case bạn vừa test: "đến hà nội và giới thiệu khách sạn"
            return "🏨 Hotel Specialist: Với Hà Nội, bạn thích khu phố cổ hay gần Hồ Tây? Ngân sách dự kiến của bạn là bao nhiêu/đêm?\n\nCONVERSATION_COMPLETE: Waiting for hotel preferences"

        # 2) Handoff sang Flight khi cần
        if any(k in user_text_lower for k in flight_kw):
            return "TRANSFER_TO_FLIGHT: User asked for flights from hotel flow"

        # 3) Còn lại -> handoff về General
        return "TRANSFER_TO_GENERAL: General/non-hotel question"

    def _extract_data_from_input(self, user_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract hotel-related data from user input"""
        data = {"user_input": user_text, "timestamp": "now"}
        
        # Extract hotel information
        if any(kw in user_text.lower() for kw in ['khách sạn', 'hotel', 'phòng', 'nghỉ']):
            data["hotel_request"] = True
            data["raw_input"] = user_text
            
            # Simple extraction (in production, use NER)
            if 'hà nội' in user_text.lower() or 'hn' in user_text.lower():
                data["city"] = "Hà Nội"
            if 'hcm' in user_text.lower() or 'hồ chí minh' in user_text.lower():
                data["city"] = "HCM"
        
        return data

    def _is_task_completed(self, collected_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if hotel task is completed"""
        return collected_data.get("hotel_request", False) and "city" in collected_data


class GeneralAssistantAgent(BaseAgent):
    """General agent that can answer general questions OR transfer to specialists"""

    def __init__(self, llm):
        super().__init__(llm, "general_assistant", GENERAL_TOOLS)

    def _get_system_prompt(self) -> str:
        return """Bạn là trợ lý du lịch tổng quát. Bạn:

1. TRẢ LỜI câu hỏi chung về du lịch, thời tiết, tư vấn
2. CHUYỂN GIAO đến specialist:
   - transfer_to_flight_specialist: khi user cần vé máy bay
   - transfer_to_hotel_specialist: khi user cần khách sạn"""

    def _process_with_llm_and_context(self, messages: List, system_prompt: str, context: Dict[str, Any], user_text: str) -> str:
        """Process general requests with context"""
        user_text_lower = user_text.lower()

        flight_kw = ['vé', 'máy bay', 'flight', 'bay', 'chuyến bay', 'đặt vé']
        hotel_kw  = ['khách sạn', 'hotel', 'phòng', 'nghỉ', 'resort', 'đặt phòng']

        # Check completion status and provide summary
        completion_status = context.get("completion_status", {})
        collected_data = context.get("collected_data", {})

        # If all agents completed, provide final summary
        if all(completion_status.values()):
            return self._generate_final_summary(collected_data)

        # Handoff rõ ràng dựa trên ý định
        if any(k in user_text_lower for k in flight_kw):
            return "TRANSFER_TO_FLIGHT: Need a flight specialist"
        if any(k in user_text_lower for k in hotel_kw):
            return "TRANSFER_TO_HOTEL: Need a hotel specialist"

        # Không handoff -> chỉ tư vấn chung
        return "💬 General Assistant: Bạn muốn đi đâu và khi nào? Mình có thể tư vấn lịch trình/chi phí/điểm đến.\n\nCONVERSATION_COMPLETE: General advice provided"

    def _extract_data_from_input(self, user_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract general travel data from user input"""
        data = {"user_input": user_text, "timestamp": "now"}
        
        # Extract general travel information
        if any(kw in user_text.lower() for kw in ['du lịch', 'travel', 'đi', 'thăm', 'khám phá']):
            data["general_travel_request"] = True
            data["raw_input"] = user_text
        
        return data

    def _is_task_completed(self, collected_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if general task is completed"""
        return collected_data.get("general_travel_request", False)

    def _generate_final_summary(self, collected_data: Dict[str, Any]) -> str:
        """Generate final summary of all collected information"""
        summary_parts = ["💬 General Assistant: Tổng kết thông tin du lịch của bạn:"]
        
        if "flight_specialist" in collected_data:
            flight_data = collected_data["flight_specialist"]
            summary_parts.append(f"✈️ Vé máy bay: {flight_data}")
        
        if "hotel_specialist" in collected_data:
            hotel_data = collected_data["hotel_specialist"]
            summary_parts.append(f"🏨 Khách sạn: {hotel_data}")
        
        if "general_assistant" in collected_data:
            general_data = collected_data["general_assistant"]
            summary_parts.append(f"💬 Thông tin chung: {general_data}")
        
        summary_parts.append("Chúc bạn có chuyến du lịch vui vẻ! 🎉")
        
        return "\n".join(summary_parts)
