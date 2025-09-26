"""
Simple test for state management without LangGraph dependencies
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Try relative import first (when run as module)
    from .state import AgentState, init_state_defaults
    from .state_manager import StateManager
    from .conversation_controller import ConversationController
except ImportError:
    # Fallback to absolute import (when run directly)
    from state import AgentState, init_state_defaults
    from state_manager import StateManager
    from conversation_controller import ConversationController
from langchain_core.messages import HumanMessage, AIMessage

def test_state_management():
    """Test state management functionality"""
    
    print("🧪 Testing State Management")
    print("=" * 40)
    
    # Test 1: Initialize state
    print("\n1. Testing state initialization...")
    state = init_state_defaults({
        "messages": [HumanMessage(content="Tôi muốn đi du lịch Hà Nội")],
        "session_id": "test_session"
    })
    
    print(f"   Initial state: {state['conversation_phase']}")
    print(f"   Required agents: {state['required_agents']}")
    print(f"   Current agent: {state['current_agent']}")
    
    # Test 2: Update conversation state
    print("\n2. Testing conversation state update...")
    state = ConversationController.update_conversation_state("Tôi muốn đi du lịch Hà Nội", state)
    
    print(f"   After analysis: {state['conversation_phase']}")
    print(f"   Required agents: {state['required_agents']}")
    print(f"   Intent: {state['intent']}")
    
    # Test 3: Agent data collection
    print("\n3. Testing agent data collection...")
    
    # Flight specialist collects data
    flight_data = {
        "origin": "HCM",
        "destination": "HN", 
        "flight_request": True,
        "raw_input": "Tôi muốn đi du lịch Hà Nội"
    }
    state = StateManager.update_agent_data("flight_specialist", flight_data, state)
    state = StateManager.mark_agent_completed("flight_specialist", state)
    
    print(f"   Flight data: {state['flight_info']}")
    print(f"   Completion status: {state['completion_status']}")
    
    # Hotel specialist collects data
    hotel_data = {
        "city": "Hà Nội",
        "hotel_request": True,
        "raw_input": "Tìm khách sạn ở Hà Nội"
    }
    state = StateManager.update_agent_data("hotel_specialist", hotel_data, state)
    state = StateManager.mark_agent_completed("hotel_specialist", state)
    
    print(f"   Hotel data: {state['hotel_info']}")
    print(f"   Completion status: {state['completion_status']}")
    
    # Test 4: Get agent context
    print("\n4. Testing agent context...")
    
    context = StateManager.get_agent_context("general_assistant", state)
    print(f"   General assistant context:")
    print(f"   - Previous agents: {context['previous_agents']}")
    print(f"   - Flight info: {context['flight_info']}")
    print(f"   - Hotel info: {context['hotel_info']}")
    print(f"   - Completion status: {context['completion_status']}")
    
    # Test 5: Determine next agent
    print("\n5. Testing next agent determination...")
    
    next_agent = StateManager.determine_next_agent(state)
    print(f"   Next agent: {next_agent}")
    
    # Test 6: Conversation continuation
    print("\n6. Testing conversation continuation...")
    
    should_continue = StateManager.should_continue_conversation(state)
    print(f"   Should continue: {should_continue}")
    
    # Mark general assistant as completed
    state = StateManager.mark_agent_completed("general_assistant", state)
    
    should_continue_after = StateManager.should_continue_conversation(state)
    print(f"   Should continue after all completed: {should_continue_after}")
    
    print("\n✅ All tests completed successfully!")

def test_conversation_flow():
    """Test conversation flow logic"""
    
    print("\n🔄 Testing Conversation Flow")
    print("=" * 40)
    
    # Simulate a conversation
    messages = [
        "Tôi muốn đi du lịch Hà Nội",
        "Tìm vé máy bay cho tôi", 
        "Giờ tìm khách sạn",
        "Có thông tin gì về thời tiết không?",
        "Quay lại tìm khách sạn khác"
    ]
    
    state = init_state_defaults({
        "messages": [],
        "session_id": "flow_test"
    })
    
    for i, message in enumerate(messages):
        print(f"\nStep {i+1}: {message}")
        
        # Add message
        state["messages"].append(HumanMessage(content=message))
        
        # Update conversation state
        state = ConversationController.update_conversation_state(message, state)
        
        # Determine next agent
        next_agent = ConversationController.get_next_agent(state)
        
        print(f"   Phase: {state['conversation_phase']}")
        print(f"   Required agents: {state['required_agents']}")
        print(f"   Next agent: {next_agent}")
        print(f"   Should continue: {ConversationController.should_continue_conversation(state)}")
        
        # Simulate agent processing
        if "vé" in message.lower() or "máy bay" in message.lower():
            flight_data = {"origin": "HCM", "destination": "HN", "flight_request": True}
            state = StateManager.update_agent_data("flight_specialist", flight_data, state)
            state = StateManager.mark_agent_completed("flight_specialist", state)
            print(f"   ✅ Flight specialist completed")
            
        elif "khách sạn" in message.lower() or "hotel" in message.lower():
            hotel_data = {"city": "Hà Nội", "hotel_request": True}
            state = StateManager.update_agent_data("hotel_specialist", hotel_data, state)
            state = StateManager.mark_agent_completed("hotel_specialist", state)
            print(f"   ✅ Hotel specialist completed")
            
        elif "thời tiết" in message.lower():
            general_data = {"weather_request": True, "destination": "Hà Nội"}
            state = StateManager.update_agent_data("general_assistant", general_data, state)
            state = StateManager.mark_agent_completed("general_assistant", state)
            print(f"   ✅ General assistant completed")

if __name__ == "__main__":
    test_state_management()
    test_conversation_flow()
