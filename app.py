import ast
import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

from openai import OpenAI


SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "When a user asks for a calculation, use the available tool instead of "
    "doing arithmetic in your head. Answer clearly and briefly."
)

ALLOWED_FUNCTIONS = {
    "abs": abs,
    "ceil": math.ceil,
    "floor": math.floor,
    "sqrt": math.sqrt,
}
ALLOWED_FUNCTION_NAMES = set(ALLOWED_FUNCTIONS) | {"round"}


def load_local_env(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def safe_calculate(expression: str) -> float:
    """Evaluate a simple arithmetic expression safely via AST."""
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Call,
        ast.Name,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.USub,
        ast.UAdd,
        ast.Constant,
        ast.Load,
    )

    tree = ast.parse(expression, mode="eval")

    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError(f"Unsupported expression element: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCTION_NAMES:
                raise ValueError(
                    "Only these functions are allowed: " + ", ".join(sorted(ALLOWED_FUNCTION_NAMES))
                )

    return _eval_node(tree.body)


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        args = [_eval_node(arg) for arg in node.args]
        if node.func.id == "round":
            if len(args) == 1:
                return float(round(args[0]))
            if len(args) == 2:
                return float(round(args[0], int(args[1])))
            raise ValueError("round accepts one or two arguments.")

        func = ALLOWED_FUNCTIONS[node.func.id]
        return float(func(*args))

    if isinstance(node, ast.UnaryOp):
        value = _eval_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value

    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)

        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left**right
        if isinstance(node.op, ast.Mod):
            return left % right

    raise ValueError("Unsupported expression.")


def run_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if tool_name != "calculate_expression":
        raise ValueError(f"Unknown tool: {tool_name}")

    expression = arguments["expression"]
    result = safe_calculate(expression)
    return {"expression": expression, "result": result}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Demo script that calls an LLM API and lets it use a local calculator tool."
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Question for the assistant. If omitted, the script asks interactively.",
    )
    parser.add_argument(
        "--show-tool-calls",
        action="store_true",
        help="Print every calculator tool call before the final answer.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    load_local_env()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "Missing OPENAI_API_KEY. Add it to a local .env file or set it as an environment variable."
        )

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)

    user_message = " ".join(args.prompt).strip()
    if not user_message:
        user_message = input("Ask something: ").strip()
    if not user_message:
        raise SystemExit("Please provide a prompt.")

    tools = [
        {
            "type": "function",
            "name": "calculate_expression",
            "description": "Evaluate a mathematical expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": (
                            "Math expression, for example: (12 + 5) * 3 or sqrt(144). "
                            "Supported operators are +, -, *, /, **, % and parentheses."
                        ),
                    }
                },
                "required": ["expression"],
                "additionalProperties": False,
            },
            "strict": True,
        }
    ]

    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=user_message,
        tools=tools,
    )

    while True:
        function_calls = [item for item in response.output if item.type == "function_call"]
        if not function_calls:
            print("\nAssistant:", response.output_text)
            break

        tool_outputs = []
        for function_call in function_calls:
            arguments = json.loads(function_call.arguments)
            result = run_tool(function_call.name, arguments)
            if args.show_tool_calls:
                print(f"Tool call: {function_call.name}({arguments}) -> {result}")
            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": function_call.call_id,
                    "output": json.dumps(result),
                }
            )

        response = client.responses.create(
            model=model,
            previous_response_id=response.id,
            input=tool_outputs,
        )


if __name__ == "__main__":
    main()
