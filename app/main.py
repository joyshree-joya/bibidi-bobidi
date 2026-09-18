import inspect
import logging
from importlib import import_module
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, status

from app.optimizer import (
    OptimizationError,
    optimize_energy_schedule,
)
from app.schemas import (
    DirectiveInterpretation,
    OptimizeEnergyRequest,
    OptimizeEnergyResponse,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="GridWise Energy Optimization API",
    description=(
        "LLM-powered smart campus energy optimization service"
    ),
    version="1.0.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _load_required_function(
    module_name: str,
    function_name: str,
) -> Callable[..., Any]:
    """
    Load teammate modules lazily.

    This allows /health to work before the LLM and guardrail branches
    have been merged.
    """

    try:
        module = import_module(module_name)
        function = getattr(module, function_name)
    except (ImportError, AttributeError) as error:
        raise RuntimeError(
            f"Required integration is unavailable: "
            f"{module_name}.{function_name}"
        ) from error

    if not callable(function):
        raise RuntimeError(
            f"Required integration is not callable: "
            f"{module_name}.{function_name}"
        )

    return function


async def _call_interpreter(
    request: OptimizeEnergyRequest,
) -> list[dict]:
    interpreter = _load_required_function(
        module_name="app.llm_interpreter",
        function_name="interpret_operator_notes",
    )

    result = interpreter(
        notes=request.operator_notes,
        battery_capacity_kwh=request.battery.capacity_kwh,
    )

    if inspect.isawaitable(result):
        result = await result

    if not isinstance(result, list):
        raise ValueError(
            "LLM interpreter must return a list of directives"
        )

    return result


def _validate_directives(
    raw_directives: list[dict],
    request: OptimizeEnergyRequest,
) -> list[DirectiveInterpretation]:
    guardrail = _load_required_function(
        module_name="app.guardrails",
        function_name="validate_and_normalize_directives",
    )

    normalized_directives = guardrail(
        raw_directives=raw_directives,
        notes_count=len(request.operator_notes),
        battery_capacity_kwh=request.battery.capacity_kwh,
    )

    if not isinstance(normalized_directives, list):
        raise ValueError(
            "Guardrail must return a list of directives"
        )

    return [
        DirectiveInterpretation.model_validate(directive)
        for directive in normalized_directives
    ]


def _build_plan_summary(
    request: OptimizeEnergyRequest,
    directives: list[DirectiveInterpretation],
    total_grid_kwh: float,
    total_cost_bdt: float,
) -> str:
    applied_count = sum(
        1
        for directive in directives
        if directive.applies
    )

    return (
        f"Generated a minimum-cost 24-hour energy plan for "
        f"scenario {request.scenario_id}. Applied "
        f"{applied_count} operator directive(s). "
        f"Total grid import is {total_grid_kwh:.2f} kWh "
        f"with an estimated cost of "
        f"{total_cost_bdt:.2f} BDT."
    )


@app.post(
    "/optimize-energy",
    response_model=OptimizeEnergyResponse,
)
async def optimize_energy(
    request: OptimizeEnergyRequest,
) -> OptimizeEnergyResponse:
    try:
        raw_directives = await _call_interpreter(request)

        directives = _validate_directives(
            raw_directives=raw_directives,
            request=request,
        )

        optimization_result = optimize_energy_schedule(
            request=request,
            directives=directives,
        )

        plan_summary = _build_plan_summary(
            request=request,
            directives=directives,
            total_grid_kwh=optimization_result.total_grid_kwh,
            total_cost_bdt=optimization_result.total_cost_bdt,
        )

        return OptimizeEnergyResponse(
            scenario_id=request.scenario_id,
            directive_interpretation=directives,
            hourly_plan=optimization_result.hourly_plan,
            total_grid_kwh=optimization_result.total_grid_kwh,
            total_cost_bdt=optimization_result.total_cost_bdt,
            peak_grid_kwh=optimization_result.peak_grid_kwh,
            plan_summary=plan_summary,
        )

    except RuntimeError as error:
        # Expected temporarily until teammate modules are merged.
        logger.warning("Required integration unavailable: %s", error)

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The directive interpretation service "
                "is not available yet."
            ),
        ) from error

    except OptimizationError as error:
        logger.warning("Optimization failed: %s", error)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A feasible optimal schedule could not be produced.",
        ) from error

    except ValueError as error:
        logger.warning("Directive validation failed: %s", error)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The interpreted directives failed validation.",
        ) from error

    except Exception as error:
        # Do not expose API keys, provider errors or stack traces.
        logger.exception("Unexpected optimization request failure")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The optimization request could not be completed.",
        ) from error