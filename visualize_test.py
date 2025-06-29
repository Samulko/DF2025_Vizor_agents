#!/usr/bin/env python3
"""
Simple test script to visualize the triage agent structure.
"""

from src.bridge_design_system.agents.triage_agent_smolagents import create_triage_system

def main():
    print("Creating triage system...")
    triage_agent = create_triage_system()
    
    print("\nVisualizing triage agent structure:")
    triage_agent.visualize()

if __name__ == "__main__":
    main()