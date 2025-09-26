"""
State Management for Agent Network Handoff
Handles state transfer and accumulation between agents
"""

from typing import Dict, Any, List
try:
    from .state import AgentState
except ImportError:
    from state import AgentState

class StateManager:
    """Manages state transfer and accumulation between agents"""
    
    @staticmethod
    def handoff_state(current_agent: str, target_agent: str, state: AgentState) -> AgentState:
        """Transfer state from current agent to target agent"""
        
        # Update agent history
        agent_history = state.get("agent_history", [])
        if current_agent not in agent_history:
            agent_history.append(current_agent)
        
        # Update current agent
        new_state = {
            **state,
            "current_agent": target_agent,
            "agent_history": agent_history
        }
        
        # Add context about handoff
        new_state["collected_data"][f"handoff_{current_agent}_to_{target_agent}"] = {
            "timestamp": "now",  # In real implementation, use actual timestamp
            "reason": f"Transferring from {current_agent} to {target_agent}",
            "previous_data": state.get("collected_data", {}).get(current_agent, {})
        }
        
        return new_state
    
    @staticmethod
    def update_agent_data(agent_name: str, data: Dict[str, Any], state: AgentState) -> AgentState:
        """Update data collected by specific agent"""
        
        collected_data = state.get("collected_data", {})
        collected_data[agent_name] = {
            **collected_data.get(agent_name, {}),
            **data
        }
        
        # Update domain-specific info
        new_state = {**state, "collected_data": collected_data}
        
        if agent_name == "flight_specialist":
            new_state["flight_info"] = {**state.get("flight_info", {}), **data}
        elif agent_name == "hotel_specialist":
            new_state["hotel_info"] = {**state.get("hotel_info", {}), **data}
        elif agent_name == "general_assistant":
            new_state["general_info"] = {**state.get("general_info", {}), **data}
        
        return new_state
    
    @staticmethod
    def mark_agent_completed(agent_name: str, state: AgentState) -> AgentState:
        """Mark an agent as completed its task"""
        
        completion_status = state.get("completion_status", {})
        completion_status[agent_name] = True
        
        return {**state, "completion_status": completion_status}
    
    @staticmethod
    def get_agent_context(agent_name: str, state: AgentState) -> Dict[str, Any]:
        """Get context for specific agent from accumulated state"""
        
        context = {
            "previous_agents": state.get("agent_history", []),
            "conversation_phase": state.get("conversation_phase", "collecting"),
            "collected_data": state.get("collected_data", {}),
            "completion_status": state.get("completion_status", {}),
            "user_preferences": state.get("user_preferences", {})
        }
        
        # Add domain-specific context
        if agent_name == "flight_specialist":
            context["flight_info"] = state.get("flight_info", {})
            context["hotel_info"] = state.get("hotel_info", {})  # For cross-domain context
        elif agent_name == "hotel_specialist":
            context["hotel_info"] = state.get("hotel_info", {})
            context["flight_info"] = state.get("flight_info", {})  # For cross-domain context
        elif agent_name == "general_assistant":
            context["general_info"] = state.get("general_info", {})
            context["flight_info"] = state.get("flight_info", {})
            context["hotel_info"] = state.get("hotel_info", {})
        
        return context
    
    @staticmethod
    def determine_next_agent(state: AgentState) -> str:
        """Determine which agent should process next based on state"""
        
        completion_status = state.get("completion_status", {})
        required_agents = state.get("required_agents", [])
        conversation_phase = state.get("conversation_phase", "collecting")
        
        # If all required agents completed, move to finalizing
        if all(completion_status.get(agent, False) for agent in required_agents):
            return "finalizing"
        
        # Find next uncompleted required agent
        for agent in required_agents:
            if not completion_status.get(agent, False):
                return agent
        
        # Default fallback
        return "general_assistant"
    
    @staticmethod
    def should_continue_conversation(state: AgentState) -> bool:
        """Determine if conversation should continue or end"""
        
        completion_status = state.get("completion_status", {})
        required_agents = state.get("required_agents", [])
        conversation_phase = state.get("conversation_phase", "collecting")
        
        # Continue if not all required agents completed
        if not all(completion_status.get(agent, False) for agent in required_agents):
            return True
        
        # Continue if in collecting or processing phase
        if conversation_phase in ["collecting", "processing"]:
            return True
        
        # End if completed
        if conversation_phase == "completed":
            return False
        
        return True
