"""
Unit tests for server/manager.py (WebSocketManager)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestWebSocketManager:
    """Tests for WebSocketManager."""

    def _make_manager(self):
        from manager import WebSocketManager
        return WebSocketManager()

    def _make_mock_ws(self, host="127.0.0.1", port=8000):
        ws = AsyncMock()
        ws.client = MagicMock()
        ws.client.host = host
        ws.client.port = port
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.receive_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()
        await mgr.connect(ws)
        ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_adds_to_connected_clients(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()
        await mgr.connect(ws)
        assert ws in mgr.connected_clients

    @pytest.mark.asyncio
    async def test_connect_sends_welcome_message(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()
        await mgr.connect(ws)
        # Check that send_json was called (welcome + broadcast join)
        calls = ws.send_json.call_args_list
        welcome_msg = calls[0][0][0]
        assert welcome_msg["type"] == "welcome"
        assert "Welcome" in welcome_msg["message"]

    @pytest.mark.asyncio
    async def test_disconnect_removes_client(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()
        await mgr.connect(ws)
        assert ws in mgr.connected_clients
        await mgr.disconnect(ws)
        assert ws not in mgr.connected_clients

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_client_no_error(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()
        # Should not raise
        await mgr.disconnect(ws)

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self):
        mgr = self._make_manager()
        ws1 = self._make_mock_ws("1.1.1.1", 1000)
        ws2 = self._make_mock_ws("2.2.2.2", 2000)
        await mgr.connect(ws1)
        await mgr.connect(ws2)
        
        msg = {"type": "test", "message": "hello all"}
        await mgr.broadcast(msg)
        
        # Both should receive the broadcast
        ws1.send_json.assert_called_with(msg)
        ws2.send_json.assert_called_with(msg)

    @pytest.mark.asyncio
    async def test_broadcast_continues_on_error(self):
        mgr = self._make_manager()
        ws1 = self._make_mock_ws()
        ws2 = self._make_mock_ws("2.2.2.2", 2000)
        await mgr.connect(ws1)
        await mgr.connect(ws2)

        # Make ws1 fail on the broadcast call
        ws1.send_json.side_effect = [None, None, Exception("connection lost")]
        
        msg = {"type": "test", "message": "hello"}
        # Should not raise
        await mgr.broadcast(msg)

    @pytest.mark.asyncio
    async def test_send_message_formats_correctly(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()
        await mgr.connect(ws)

        raw_msg = {"client": "user1", "content": "Hello!", "timestamp": "2026-01-01T00:00:00"}
        await mgr.send_message(ws, raw_msg)

        last_call = ws.send_json.call_args_list[-1][0][0]
        assert last_call["type"] == "chat"
        assert last_call["client"] == "user1"
        assert last_call["message"] == "Hello!"

    @pytest.mark.asyncio
    async def test_send_message_uses_message_key_fallback(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()
        await mgr.connect(ws)

        raw_msg = {"client": "user1", "message": "Hello via message key"}
        await mgr.send_message(ws, raw_msg)

        last_call = ws.send_json.call_args_list[-1][0][0]
        assert last_call["message"] == "Hello via message key"

    @pytest.mark.asyncio
    async def test_send_message_defaults_unknown_client(self):
        mgr = self._make_manager()
        ws = self._make_mock_ws()
        await mgr.connect(ws)

        raw_msg = {"content": "msg without client"}
        await mgr.send_message(ws, raw_msg)

        last_call = ws.send_json.call_args_list[-1][0][0]
        assert last_call["client"] == "Unknown"

    @pytest.mark.asyncio
    async def test_multiple_connect_disconnect_cycle(self):
        mgr = self._make_manager()
        clients = [self._make_mock_ws(f"{i}.0.0.1", i) for i in range(5)]
        
        for ws in clients:
            await mgr.connect(ws)
        assert len(mgr.connected_clients) == 5
        
        for ws in clients[:3]:
            await mgr.disconnect(ws)
        assert len(mgr.connected_clients) == 2
