"""Unit tests for command registry."""

import pytest
from unittest.mock import MagicMock

from aimino_frontend.aimino_core.registry import (
    register_handler,
    dispatch,
    available_actions,
    COMMAND_REGISTRY,
)
from aimino_frontend.aimino_core.errors import CommandExecutionError


@pytest.mark.unit
class TestRegistry:
    """Test command registry functionality."""

    def test_register_handler(self):
        """Test registering a handler."""
        # Clear registry for clean test
        COMMAND_REGISTRY.clear()
        
        @register_handler("test_action")
        def test_handler(command, viewer):
            return "test result"
        
        assert "test_action" in COMMAND_REGISTRY
        assert COMMAND_REGISTRY["test_action"] == test_handler

    def test_register_handler_duplicate(self):
        """Test that registering duplicate handler raises error."""
        COMMAND_REGISTRY.clear()
        
        @register_handler("duplicate_action")
        def handler1(command, viewer):
            return "handler1"
        
        # Try to register another handler for the same action
        with pytest.raises(ValueError, match="already registered"):
            @register_handler("duplicate_action")
            def handler2(command, viewer):
                return "handler2"

    def test_dispatch_existing_action(self):
        """Test dispatching an existing action."""
        COMMAND_REGISTRY.clear()
        
        @register_handler("existing_action")
        def handler(command, viewer):
            return "success"
        
        handler_func = dispatch("existing_action")
        assert handler_func is not None
        assert callable(handler_func)
        
        mock_viewer = MagicMock()
        result = handler_func(MagicMock(), mock_viewer)
        assert result == "success"

    def test_dispatch_nonexistent_action(self):
        """Test dispatching a nonexistent action raises error."""
        COMMAND_REGISTRY.clear()
        
        with pytest.raises(CommandExecutionError, match="Unsupported action"):
            dispatch("nonexistent_action")

    def test_available_actions(self):
        """Test getting list of available actions."""
        COMMAND_REGISTRY.clear()
        
        @register_handler("action1")
        def handler1(command, viewer):
            return "result1"
        
        @register_handler("action2")
        def handler2(command, viewer):
            return "result2"
        
        actions = available_actions()
        assert "action1" in actions
        assert "action2" in actions
        assert isinstance(actions, list)
        # Should be sorted
        assert actions == sorted(actions)



