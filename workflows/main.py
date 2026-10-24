"""Render Workflows entrypoint. Registration is not deployment or a cloud run.

From repository root: python workflows/main.py
Only run through Render's local CLI task server or an explicitly deployed service.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from render import Retry, TaskContext, Workflows
from revivegraph import workflow

NO_RETRY = Retry(max_retries=0, wait_duration_ms=1000)
app = Workflows(default_retry=NO_RETRY, default_timeout=900, default_plan="flex")


@app.task(name="validate_input", retry=NO_RETRY, timeout_seconds=90)
def validate_input(ctx: TaskContext, value: dict) -> dict:
    return workflow.validate_input(value)


@app.task(name="execute_plan", retry=NO_RETRY, timeout_seconds=900)
def execute_plan(ctx: TaskContext, value: dict) -> dict:
    # A Nodus submission is billable. Neither this task nor its parent retries.
    # Nodus itself also keeps a conservative per-request attempt receipt.
    return workflow.execute_plan(value)


@app.task(name="validate_result", retry=NO_RETRY, timeout_seconds=90)
def validate_result(ctx: TaskContext, value: dict) -> dict:
    return workflow.validate_result(value)


@app.task(name="generate_audit", retry=NO_RETRY, timeout_seconds=30)
def generate_audit(ctx: TaskContext, value: dict) -> dict:
    return workflow.generate_audit(value)


@app.task(name="recover", retry=NO_RETRY, timeout_seconds=1200)
async def recover(ctx: TaskContext, value: dict) -> dict:
    state = await ctx.run(validate_input, value)
    state = await ctx.run(execute_plan, state)
    state = await ctx.run(validate_result, state)
    state = await ctx.run(generate_audit, state)
    workflow.finish(state, "render-workflows")
    # Return the complete hashed stage envelope. The caller revalidates it
    # against its original request before it accepts or persists any allocation.
    return state


if __name__ == "__main__":
    app.start()
