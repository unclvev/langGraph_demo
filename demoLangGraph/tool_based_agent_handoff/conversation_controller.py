"""
Conversation Flow Controller for Agent Network
Manages the flow of conversation between agents based on user intent and collected data
"""

from typing import Dict, Any, List
try:
    from .state import AgentState
    from .state_manager import StateManager
except ImportError:
    from state import AgentState
    from state_manager import StateManager

class ConversationController:
    """Controls conversation flow between agents"""
    
    @staticmethod
    def analyze_user_intent(user_text: str, state: AgentState) -> Dict[str, Any]:
        """Analyze user intent and determine required agents"""
        
        user_text_lower = user_text.lower()
        
        # Keywords for different domains
        flight_keywords = ['vé', 'máy bay', 'flight', 'bay', 'chuyến bay', 'đặt vé']
        hotel_keywords = ['khách sạn', 'hotel', 'phòng', 'nghỉ', 'resort', 'đặt phòng']
        general_keywords = ['du lịch', 'travel', 'đi', 'thăm', 'khám phá', 'tư vấn']
        
        # Determine which domains are mentioned
        requires_flight = any(kw in user_text_lower for kw in flight_keywords)
        requires_hotel = any(kw in user_text_lower for kw in hotel_keywords)
        requires_general = any(kw in user_text_lower for kw in general_keywords)
        
        # If no specific domain mentioned, assume general travel planning
        if not requires_flight and not requires_hotel and not requires_general:
            requires_general = True
        
        # Determine required agents
        required_agents = []
        if requires_flight:
            required_agents.append("flight_specialist")
        if requires_hotel:
            required_agents.append("hotel_specialist")
        if requires_general:
            required_agents.append("general_assistant")
        
        return {
            "requires_flight": requires_flight,
            "requires_hotel": requires_hotel,
            "requires_general": requires_general,
            "required_agents": required_agents,
            "intent": "travel_planning" if len(required_agents) > 1 else "single_domain"
        }
    
    @staticmethod
    def determine_conversation_phase(state: AgentState) -> str:
        """Determine current conversation phase based on state"""
        
        completion_status = state.get("completion_status", {})
        required_agents = state.get("required_agents", [])
        agent_history = state.get("agent_history", [])
        
        # If no required agents set, still collecting
        if not required_agents:
            return "collecting"
        
        # If all required agents completed
        if all(completion_status.get(agent, False) for agent in required_agents):
            return "completed"
        
        # If some agents completed but not all
        completed_count = sum(1 for agent in required_agents if completion_status.get(agent, False))
        if completed_count > 0:
            return "processing"
        
        # Still collecting
        return "collecting"
    
    @staticmethod
    def should_continue_conversation(state: AgentState) -> bool:
        """Determine if conversation should continue"""
        
        conversation_phase = ConversationController.determine_conversation_phase(state)
        completion_status = state.get("completion_status", {})
        required_agents = state.get("required_agents", [])
        
        # Continue if not all required agents completed
        if not all(completion_status.get(agent, False) for agent in required_agents):
            return True
        
        # Continue if in collecting or processing phase
        if conversation_phase in ["collecting", "processing"]:
            return True
        
        # End if completed
        return conversation_phase != "completed"
    
    @staticmethod
    def get_next_agent(state: AgentState) -> str:
        """Get the next agent that should process the request"""
        
        completion_status = state.get("completion_status", {})
        required_agents = state.get("required_agents", [])
        current_agent = state.get("current_agent", "general_assistant")
        
        # If no required agents set, start with general assistant
        if not required_agents:
            return "general_assistant"
        
        # Find next uncompleted required agent
        for agent in required_agents:
            if not completion_status.get(agent, False):
                return agent
        
        # If all required agents completed, let general assistant finalize
        return "general_assistant"
    
    @staticmethod
    def update_conversation_state(user_text: str, state: AgentState) -> AgentState:
        """Update conversation state based on user input"""
        
        # Analyze user intent
        intent_analysis = ConversationController.analyze_user_intent(user_text, state)
        
        # Update required agents if not set
        if not state.get("required_agents"):
            state["required_agents"] = intent_analysis["required_agents"]
        
        # Update conversation phase
        state["conversation_phase"] = ConversationController.determine_conversation_phase(state)
        
        # Update intent
        state["intent"] = intent_analysis["intent"]
        
        return state
    
    @staticmethod
    def generate_agent_context(agent_name: str, state: AgentState) -> Dict[str, Any]:
        """Generate context for specific agent"""
        
        context = StateManager.get_agent_context(agent_name, state)
        
        # Add conversation flow context
        context["conversation_phase"] = state.get("conversation_phase", "collecting")
        context["required_agents"] = state.get("required_agents", [])
        context["intent"] = state.get("intent", "")
        
        # Add handoff history
        context["handoff_history"] = state.get("agent_history", [])
        
        return context
