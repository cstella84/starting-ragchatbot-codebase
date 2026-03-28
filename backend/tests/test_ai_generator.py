import pytest
from unittest.mock import MagicMock, patch, call
from ai_generator import AIGenerator


def make_text_block(text="Final answer."):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def make_tool_use_block(tool_id="tool_1", name="search_course_content", input=None):
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = name
    block.input = input or {"query": "test query"}
    return block


def make_response(stop_reason, content_blocks):
    response = MagicMock()
    response.stop_reason = stop_reason
    response.content = content_blocks
    return response


@pytest.fixture
def generator():
    with patch("anthropic.Anthropic"):
        gen = AIGenerator(api_key="test-key", model="claude-test")
        return gen


@pytest.fixture
def tool_manager():
    tm = MagicMock()
    tm.execute_tool.return_value = "search result"
    return tm


TOOLS = [{"name": "search_course_content"}]


class TestDirectAnswer:
    def test_no_tools_provided(self, generator):
        """No tools → single API call, text returned."""
        generator.client.messages.create.return_value = make_response(
            "end_turn", [make_text_block("Hello.")]
        )
        result = generator.generate_response("What is Python?")
        assert result == "Hello."
        assert generator.client.messages.create.call_count == 1
        call_kwargs = generator.client.messages.create.call_args[1]
        assert "tools" not in call_kwargs

    def test_tools_provided_but_claude_answers_directly(self, generator, tool_manager):
        """Tools available but Claude returns end_turn immediately."""
        generator.client.messages.create.return_value = make_response(
            "end_turn", [make_text_block("Direct answer.")]
        )
        result = generator.generate_response(
            "What is Python?", tools=TOOLS, tool_manager=tool_manager
        )
        assert result == "Direct answer."
        assert generator.client.messages.create.call_count == 1
        tool_manager.execute_tool.assert_not_called()


class TestSingleToolRound:
    def test_one_tool_call_then_answer(self, generator, tool_manager):
        """Round 1: tool_use → execute → Round 2: end_turn answer."""
        tool_block = make_tool_use_block()
        generator.client.messages.create.side_effect = [
            make_response("tool_use", [tool_block]),
            make_response("end_turn", [make_text_block("Result based on search.")]),
        ]
        result = generator.generate_response(
            "Find a course on Python.", tools=TOOLS, tool_manager=tool_manager
        )
        assert result == "Result based on search."
        assert generator.client.messages.create.call_count == 2
        tool_manager.execute_tool.assert_called_once_with(
            "search_course_content", **tool_block.input
        )

    def test_claude_stops_voluntarily_after_round_1(self, generator, tool_manager):
        """Claude uses 1 tool round and stops even though budget allows 2."""
        tool_block = make_tool_use_block()
        generator.client.messages.create.side_effect = [
            make_response("tool_use", [tool_block]),
            make_response("end_turn", [make_text_block("Voluntary stop.")]),
        ]
        result = generator.generate_response(
            "Find a course.", tools=TOOLS, tool_manager=tool_manager
        )
        assert result == "Voluntary stop."
        # Only 2 calls: 1 tool round + 1 direct answer (no forced 3rd call)
        assert generator.client.messages.create.call_count == 2


class TestTwoToolRounds:
    def test_two_tool_rounds_then_forced_final(self, generator, tool_manager):
        """Rounds 1 & 2 both use tools; 3rd call is forced final without tools."""
        tool_block_1 = make_tool_use_block("tool_1", input={"query": "outline"})
        tool_block_2 = make_tool_use_block("tool_2", input={"query": "content"})
        generator.client.messages.create.side_effect = [
            make_response("tool_use", [tool_block_1]),
            make_response("tool_use", [tool_block_2]),
            make_response("end_turn", [make_text_block("Combined answer.")]),
        ]
        result = generator.generate_response(
            "Compare courses.", tools=TOOLS, tool_manager=tool_manager
        )
        assert result == "Combined answer."
        assert generator.client.messages.create.call_count == 3
        assert tool_manager.execute_tool.call_count == 2

    def test_final_call_has_no_tools_after_two_rounds(self, generator, tool_manager):
        """After MAX_TOOL_ROUNDS, the forced final API call must not include tools."""
        tool_block_1 = make_tool_use_block("tool_1")
        tool_block_2 = make_tool_use_block("tool_2")
        generator.client.messages.create.side_effect = [
            make_response("tool_use", [tool_block_1]),
            make_response("tool_use", [tool_block_2]),
            make_response("end_turn", [make_text_block("Final.")]),
        ]
        generator.generate_response("Query.", tools=TOOLS, tool_manager=tool_manager)

        final_call_kwargs = generator.client.messages.create.call_args_list[2][1]
        assert "tools" not in final_call_kwargs
        assert "tool_choice" not in final_call_kwargs

    def test_messages_grow_correctly_across_two_rounds(self, generator, tool_manager):
        """After 2 rounds, messages list has 5 entries: user + (assistant + tool_results) × 2."""
        tool_block_1 = make_tool_use_block("tool_1")
        tool_block_2 = make_tool_use_block("tool_2")
        generator.client.messages.create.side_effect = [
            make_response("tool_use", [tool_block_1]),
            make_response("tool_use", [tool_block_2]),
            make_response("end_turn", [make_text_block("Done.")]),
        ]
        generator.generate_response("Query.", tools=TOOLS, tool_manager=tool_manager)

        final_messages = generator.client.messages.create.call_args_list[2][1]["messages"]
        assert len(final_messages) == 5
        assert final_messages[0]["role"] == "user"      # original query
        assert final_messages[1]["role"] == "assistant" # round 1 tool_use
        assert final_messages[2]["role"] == "user"      # round 1 tool_result
        assert final_messages[3]["role"] == "assistant" # round 2 tool_use
        assert final_messages[4]["role"] == "user"      # round 2 tool_result


class TestErrorHandling:
    def test_tool_exception_does_not_propagate(self, generator, tool_manager):
        """Tool raising an exception must not propagate — final answer returned."""
        tool_block = make_tool_use_block()
        tool_manager.execute_tool.side_effect = Exception("DB connection failed")
        generator.client.messages.create.side_effect = [
            make_response("tool_use", [tool_block]),
            make_response("end_turn", [make_text_block("Sorry, error occurred.")]),
        ]
        result = generator.generate_response(
            "Find course.", tools=TOOLS, tool_manager=tool_manager
        )
        assert result == "Sorry, error occurred."

    def test_tool_error_result_forwarded_to_claude(self, generator, tool_manager):
        """Error result with is_error=True is included in messages so Claude can explain."""
        tool_block = make_tool_use_block("err_tool")
        tool_manager.execute_tool.side_effect = Exception("timeout")
        generator.client.messages.create.side_effect = [
            make_response("tool_use", [tool_block]),
            make_response("end_turn", [make_text_block("Explanation.")]),
        ]
        generator.generate_response("Find course.", tools=TOOLS, tool_manager=tool_manager)

        second_call_messages = generator.client.messages.create.call_args_list[1][1]["messages"]
        tool_result_msg = second_call_messages[-1]
        assert tool_result_msg["role"] == "user"
        error_result = tool_result_msg["content"][0]
        assert error_result["is_error"] is True
        assert "timeout" in error_result["content"]

    def test_tool_error_forces_final_call_without_tools(self, generator, tool_manager):
        """When a tool errors, the follow-up call must not include tools."""
        tool_block = make_tool_use_block()
        tool_manager.execute_tool.side_effect = Exception("fail")
        generator.client.messages.create.side_effect = [
            make_response("tool_use", [tool_block]),
            make_response("end_turn", [make_text_block("Error response.")]),
        ]
        generator.generate_response("Find course.", tools=TOOLS, tool_manager=tool_manager)

        final_call_kwargs = generator.client.messages.create.call_args_list[1][1]
        assert "tools" not in final_call_kwargs


class TestSystemPrompt:
    def test_system_prompt_allows_sequential_tool_calls(self):
        assert "One search per query maximum" not in AIGenerator.SYSTEM_PROMPT

    def test_system_prompt_mentions_multiple_tool_calls(self):
        prompt_lower = AIGenerator.SYSTEM_PROMPT.lower()
        assert "2" in prompt_lower or "sequential" in prompt_lower or "two" in prompt_lower

    def test_conversation_history_included_in_system(self, generator, tool_manager):
        """Conversation history is appended to the system prompt."""
        generator.client.messages.create.return_value = make_response(
            "end_turn", [make_text_block("Answer.")]
        )
        generator.generate_response(
            "Question?",
            conversation_history="User: Hi\nAssistant: Hello",
            tools=TOOLS,
            tool_manager=tool_manager,
        )
        system_arg = generator.client.messages.create.call_args[1]["system"]
        assert "User: Hi" in system_arg
        assert AIGenerator.SYSTEM_PROMPT.strip()[:30] in system_arg
