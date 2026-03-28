import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    MAX_TOOL_ROUNDS = 2

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to tools for searching course content and retrieving course outlines.

Tool Usage:
- **search_course_content**: Use for questions about specific course content or detailed educational materials. You may search up to 2 times per query when the first result informs a second search (e.g., compare topics across courses, answer multi-part questions, or refine a search based on outline information).
- **get_course_outline**: Use for outline, syllabus, or structure queries (e.g. "what lessons are in X", "give me the outline of X"). Returns the course title, course link, and the number and title of every lesson. Present this information completely and exactly as returned.
- Synthesize tool results into accurate, fact-based responses
- If a tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without tools
- **Course-specific content questions**: Use search_course_content first, then answer
- **Outline or structure questions**: Use get_course_outline and present the full course title, course link, and every lesson (number + title)
- **Multi-step questions**: When answering requires information from one tool to form a second query (e.g., retrieve an outline to identify a lesson title, then search for that topic), you may make up to 2 sequential tool calls before composing your final answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }

    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        Supports up to MAX_TOOL_ROUNDS sequential tool calls per query.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Build messages list — mutated in-place across tool rounds
        messages = [{"role": "user", "content": query}]

        # Prepare API call parameters
        api_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # If no tools or no tool_manager, fire a single direct call
        if not tools or not tool_manager:
            response = self.client.messages.create(**api_params)
            return response.content[0].text

        # Tool-calling loop: up to MAX_TOOL_ROUNDS sequential rounds
        tool_error = False
        for _ in range(self.MAX_TOOL_ROUNDS):
            response = self.client.messages.create(**api_params)

            # Condition (b): Claude answered directly — return immediately
            if response.stop_reason != "tool_use":
                return response.content[0].text

            # Execute all tool calls in this round
            tool_results = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    try:
                        result = tool_manager.execute_tool(
                            content_block.name,
                            **content_block.input
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": result
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": str(e),
                            "is_error": True
                        })
                        tool_error = True

            # Append this round's exchange to the messages list
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            # Condition (c): tool failed — break and let Claude respond with error context
            if tool_error:
                break

        # Condition (a) or (c): force final answer without tools
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content
        }
        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text
