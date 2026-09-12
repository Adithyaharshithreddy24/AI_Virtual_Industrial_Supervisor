import json
from typing import Any

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from app.core.config import get_settings
from app.models.schemas import (
    SourceDocument,
    SupervisorDecision,
)
from app.prompts.supervisor import SUPERVISOR_SYSTEM_PROMPT
from app.tools.rag_tools import search_manual
from app.tools.technician_tools import alert_technician


class IndustrialSupervisor:
    """Orchestrates the Gemini tool-calling supervisor workflow."""

    def __init__(self) -> None:
        settings = get_settings()

        self.settings = settings

        if settings.llm_provider.lower() == "ollama":
            from langchain_ollama import ChatOllama

            self.model = ChatOllama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=settings.llm_temperature,
                num_predict=settings.llm_max_tokens,
            )
        else:
            from langchain_google_genai import ChatGoogleGenerativeAI

            if not settings.google_api_key:
                raise RuntimeError(
                    "GOOGLE_API_KEY is not configured"
                )

            self.model = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=settings.llm_temperature,
                max_output_tokens=settings.llm_max_tokens,
            )

        self.tools = [
            search_manual,
            alert_technician,
        ]

        self.tools_by_name = {
            tool.name: tool
            for tool in self.tools
        }

    # ============================================================
    # TOOL RESULT SERIALIZATION
    # ============================================================

    @staticmethod
    def _serialize_tool_result(result: Any) -> str:
        """
        Convert any LangChain/tool result into safe text
        that can be placed inside a ToolMessage.
        """

        # Normal string
        if isinstance(result, str):
            return result

        # LangChain message object
        if hasattr(result, "content"):
            content = result.content

            if isinstance(content, str):
                return content

            try:
                return json.dumps(
                    content,
                    default=str,
                )
            except (TypeError, ValueError):
                return str(content)

        # Dictionary / list / normal JSON-compatible objects
        try:
            return json.dumps(
                result,
                default=str,
            )
        except (TypeError, ValueError):
            return str(result)

    # ============================================================
    # PARSE TOOL RESULT
    # ============================================================

    @staticmethod
    def _parse_tool_result(result: Any) -> dict:
        """
        Convert a tool result into a dictionary when possible.
        """

        # LangChain ToolMessage
        if hasattr(result, "content"):
            result = result.content

        # Already a dictionary
        if isinstance(result, dict):
            return result

        # JSON string
        if isinstance(result, str):
            try:
                parsed = json.loads(result)

                if isinstance(parsed, dict):
                    return parsed

            except (json.JSONDecodeError, TypeError):
                pass

        return {}

    # ============================================================
    # RUN GEMINI + TOOLS
    # ============================================================

    def _run_tools(
        self,
        messages: list[Any],
        technician_language: str = "en-IN",
        technician_phone_number: str = "",
    ) -> tuple[list[Any], list[dict]]:

        model = self.model.bind_tools(
            self.tools
        )

        tool_results: list[dict] = []

        # Prevent an infinite tool-calling loop
        for _ in range(3):

            response = model.invoke(
                messages
            )

            messages.append(
                response
            )

            # Gemini has finished tool calling
            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:

                name = tool_call["name"]

                tool = self.tools_by_name.get(
                    name
                )

                # ------------------------------------------------
                # UNKNOWN TOOL
                # ------------------------------------------------

                if tool is None:

                    result = {
                        "success": False,
                        "error": (
                            f"Unknown tool: {name}"
                        ),
                    }

                # ------------------------------------------------
                # EXECUTE TOOL
                # ------------------------------------------------

                else:

                    try:

                        tool_args = tool_call.get(
                            "args",
                            {},
                        )

                        if name == "alert_technician":
                            tool_args["language_code"] = (
                                technician_language
                            )
                            if technician_phone_number:
                                tool_args[
                                    "technician_phone_number"
                                ] = technician_phone_number

                        result = tool.invoke(
                            tool_args
                        )

                    except Exception as exc:

                        result = {
                            "success": False,
                            "error": str(exc),
                        }

                # ------------------------------------------------
                # SAVE RAW TOOL RESULT
                # ------------------------------------------------

                tool_results.append(
                    {
                        "name": name,
                        "result": result,
                    }
                )

                # ------------------------------------------------
                # CONVERT RESULT TO SAFE TEXT
                # ------------------------------------------------

                tool_content = (
                    self._serialize_tool_result(
                        result
                    )
                )

                # ------------------------------------------------
                # SEND RESULT BACK TO GEMINI
                # ------------------------------------------------

                messages.append(
                    ToolMessage(
                        content=tool_content,
                        tool_call_id=tool_call["id"],
                    )
                )

        return (
            messages,
            tool_results,
        )

    # ============================================================
    # EXTRACT MANUAL SOURCES
    # ============================================================

    @staticmethod
    def _extract_sources(
        tool_results: list[dict],
    ) -> list[SourceDocument]:

        sources: list[SourceDocument] = []

        seen: set[
            tuple[str, int, str]
        ] = set()

        for item in tool_results:

            if item["name"] != "search_manual":
                continue

            raw = item["result"]

            # Convert ToolMessage -> content
            if hasattr(raw, "content"):
                raw = raw.content

            # Parse result
            if isinstance(raw, dict):

                payload = raw

            elif isinstance(raw, str):

                try:

                    payload = json.loads(
                        raw
                    )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):
                    continue

            else:
                continue

            # Make sure payload is a dictionary
            if not isinstance(
                payload,
                dict,
            ):
                continue

            for source in payload.get(
                "sources",
                [],
            ):

                if not isinstance(
                    source,
                    dict,
                ):
                    continue

                key = (
                    source.get(
                        "file",
                        "unknown",
                    ),
                    int(
                        source.get(
                            "page",
                            0,
                        )
                    ),
                    source.get(
                        "chunk_excerpt",
                        "",
                    ),
                )

                if key in seen:
                    continue

                seen.add(key)

                try:

                    sources.append(
                        SourceDocument(
                            **source
                        )
                    )

                except Exception:
                    # Ignore malformed source entries
                    continue

        return sources

    # ============================================================
    # ANALYZE OPERATOR ISSUE
    # ============================================================

    def analyze(
        self,
        operator_message: str,
        domain_filter: str | None = None,
        technician_language: str = "en-IN",
        technician_phone_number: str = "",
    ) -> SupervisorDecision:

        # --------------------------------------------------------
        # VALIDATE INPUT
        # --------------------------------------------------------

        if not operator_message.strip():

            raise ValueError(
                "Operator message cannot be empty"
            )

        # --------------------------------------------------------
        # BUILD USER PROMPT
        # --------------------------------------------------------

        user_prompt = (
            "Operator report:\n"
            f"{operator_message.strip()}\n\n"
            "Manual domain filter:\n"
            f"{domain_filter or 'none'}\n\n"
            "Analyze the issue. Search the manuals "
            "if machine-specific information is useful. "
            "Escalate to the technician when required "
            "by the safety rules."
        )

        # --------------------------------------------------------
        # INITIAL MESSAGES
        # --------------------------------------------------------

        messages: list[Any] = [

            SystemMessage(
                content=SUPERVISOR_SYSTEM_PROMPT
            ),

            HumanMessage(
                content=user_prompt
            ),

        ]

        # --------------------------------------------------------
        # GEMINI TOOL-CALLING LOOP
        # --------------------------------------------------------

        messages, tool_results = (
            self._run_tools(
                messages,
                technician_language=technician_language,
                technician_phone_number=technician_phone_number,
            )
        )

        # --------------------------------------------------------
        # FINAL STRUCTURED OUTPUT
        # --------------------------------------------------------

        final_model = (
            self.model.with_structured_output(
                SupervisorDecision
            )
        )

        final_messages = (
            messages
            + [
                HumanMessage(
                    content=(
                        "Return the final "
                        "SupervisorDecision now. "
                        "Use the tool results above. "
                        "Do not invent sources or claim "
                        "that a technician was contacted "
                        "unless the alert_technician tool "
                        "returned success."
                    )
                )
            ]
        )

        decision = (
            final_model.invoke(
                final_messages
            )
        )

        # --------------------------------------------------------
        # ATTACH MANUAL SOURCES
        # --------------------------------------------------------

        decision.manual_sources = (
            self._extract_sources(
                tool_results
            )
        )

        # --------------------------------------------------------
        # PROCESS TECHNICIAN ALERT
        # --------------------------------------------------------

        technician_results = [
            item
            for item in tool_results
            if item["name"]
            == "alert_technician"
        ]

        if technician_results:

            raw_result = (
                technician_results[-1]["result"]
            )

            payload = (
                self._parse_tool_result(
                    raw_result
                )
            )

            decision.technician_alert_sent = (
                bool(
                    payload.get(
                        "success",
                        False,
                    )
                )
            )

            decision.technician_call_sid = (
                payload.get(
                    "call_sid"
                )
            )

        else:

            decision.technician_alert_sent = False
            decision.technician_call_sid = None

        # --------------------------------------------------------
        # NORMALIZE CONFIDENCE
        # --------------------------------------------------------

        decision.confidence = max(
            0.0,
            min(
                1.0,
                float(
                    decision.confidence
                ),
            ),
        )

        # --------------------------------------------------------
        # WORKER RESOLUTION LOGIC
        # --------------------------------------------------------

        if decision.worker_can_resolve:

            decision.technician_message = None

        elif not decision.technician_message:

            decision.technician_message = (
                operator_message
            )

        # --------------------------------------------------------
        # RETURN FINAL DECISION
        # --------------------------------------------------------

        return decision