#!/usr/bin/env python3
"""Test suite for Nexus A2A Orchestration Extension v2.0."""

import os
import sys
import unittest
from unittest.mock import Mock

class TestA2AOrchestration(unittest.TestCase):
    """Test A2A orchestration components."""

    def setUp(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    def test_profile_manager_orchestration(self):
        """Test profile manager with orchestration."""
        try:
            from nexus.nexus_base.profile_manager import ProfileManager, AgentProfile

            profile = AgentProfile(
                name="TestOrchestrator", avatar="🎭", persona="Test",
                actions=[], knowledge=None, memory=None, evaluators=None,
                reasoners=None, planners=None, feedback=None,
                orchestration={"agent_urls": "http://localhost:8001"}
            )

            self.assertEqual(profile.name, "TestOrchestrator")
            self.assertIsNotNone(profile.orchestration)
            print("✅ ProfileManager test passed")
            return True
        except Exception as e:
            print(f"❌ ProfileManager test failed: {e}")
            return False

    def test_orchestration_actions_import(self):
        """Test orchestration actions import."""
        try:
            from nexus.nexus_base.nexus_actions.orchestration_actions import (
                initialize_orchestration, orchestrate, delegate_to_agent
            )
            print("✅ Orchestration actions import passed")
            return True
        except Exception as e:
            print(f"❌ Orchestration actions import failed: {e}")
            return False

def run_tests():
    """Run all tests."""
    print("🧪 Running Nexus A2A Orchestration Tests")
    print("=" * 50)

    test_suite = TestA2AOrchestration()
    tests = [
        ("Profile Manager", test_suite.test_profile_manager_orchestration),
        ("Orchestration Actions", test_suite.test_orchestration_actions_import),
    ]

    passed = failed = 0
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1

    print(f"\n📊 Results: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
