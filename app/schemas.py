from enum import Enum
from math import isfinite
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
    )


# =========================================================
# Request models
# =========================================================

class HourInput(StrictBaseModel):
    hour: int = Field(ge=0, le=23)
    demand_kwh: float = Field(ge=0)
    solar_kwh: float = Field(ge=0)
    tariff_bdt_per_kwh: float = Field(ge=0)


class BatteryInput(StrictBaseModel):
    capacity_kwh: float = Field(gt=0)
    initial_energy_kwh: float = Field(ge=0)
    minimum_energy_kwh: float = Field(ge=0)
    max_charge_kwh_per_hour: float = Field(gt=0)
    max_discharge_kwh_per_hour: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_battery_configuration(self):
        if self.minimum_energy_kwh > self.capacity_kwh:
            raise ValueError(
                "minimum_energy_kwh cannot exceed capacity_kwh"
            )

        if self.initial_energy_kwh > self.capacity_kwh:
            raise ValueError(
                "initial_energy_kwh cannot exceed capacity_kwh"
            )

        if self.initial_energy_kwh < self.minimum_energy_kwh:
            raise ValueError(
                "initial_energy_kwh cannot be below minimum_energy_kwh"
            )

        return self


class OptimizeEnergyRequest(StrictBaseModel):
    scenario_id: str = Field(min_length=1, max_length=100)
    operator_notes: list[str] = Field(min_length=1, max_length=3)
    hours: list[HourInput]
    battery: BatteryInput

    @field_validator("scenario_id")
    @classmethod
    def validate_scenario_id(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("scenario_id cannot be empty")

        return cleaned_value

    @field_validator("operator_notes")
    @classmethod
    def validate_operator_notes(cls, notes: list[str]) -> list[str]:
        cleaned_notes: list[str] = []

        for note in notes:
            if not isinstance(note, str):
                raise ValueError("Every operator note must be a string")

            cleaned_note = note.strip()

            if not cleaned_note:
                raise ValueError("Operator notes cannot be empty")

            cleaned_notes.append(cleaned_note)

        return cleaned_notes

    @model_validator(mode="after")
    def validate_24_hour_input(self):
        if len(self.hours) != 24:
            raise ValueError("hours must contain exactly 24 entries")

        hour_values = [item.hour for item in self.hours]

        if len(set(hour_values)) != 24:
            raise ValueError("Each hour must appear exactly once")

        if set(hour_values) != set(range(24)):
            raise ValueError("hours must contain every hour from 0 to 23")

        # Normalize input order so downstream code always receives 0 → 23.
        self.hours.sort(key=lambda item: item.hour)

        return self


# =========================================================
# Directive models
# =========================================================

class DirectiveType(str, Enum):
    SOLAR_REDUCTION = "solar_reduction"
    MINIMUM_BATTERY_RESERVE = "minimum_battery_reserve"
    NO_CHARGE_WINDOW = "no_charge_window"
    NO_DISCHARGE_WINDOW = "no_discharge_window"
    MAX_GRID_WINDOW = "max_grid_window"
    NO_OP = "no_op"


class SolarReductionAdjustment(StrictBaseModel):
    hours: list[int]
    factor: float = Field(ge=0, le=1)


class MinimumBatteryReserveAdjustment(StrictBaseModel):
    hours: list[int]
    minimum_energy_kwh: float = Field(ge=0)


class NoChargeAdjustment(StrictBaseModel):
    hours: list[int]


class NoDischargeAdjustment(StrictBaseModel):
    hours: list[int]


class MaxGridAdjustment(StrictBaseModel):
    hours: list[int]
    max_grid_kwh: float = Field(ge=0)


DirectiveAdjustment = (
    SolarReductionAdjustment
    | MinimumBatteryReserveAdjustment
    | NoChargeAdjustment
    | NoDischargeAdjustment
    | MaxGridAdjustment
)


class DirectiveInterpretation(StrictBaseModel):
    note_index: int = Field(ge=0)
    applies: bool
    directive_type: DirectiveType
    structured_adjustment: DirectiveAdjustment | None
    explanation: str = Field(min_length=1)


# =========================================================
# Response models
# =========================================================

class BatteryAction(str, Enum):
    CHARGE = "charge"
    DISCHARGE = "discharge"
    IDLE = "idle"


class HourlyPlanItem(StrictBaseModel):
    hour: int = Field(ge=0, le=23)
    grid_kwh: float = Field(ge=0)
    solar_used_kwh: float = Field(ge=0)
    battery_action: BatteryAction
    battery_kwh: float = Field(ge=0)
    battery_energy_after_kwh: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_battery_action(self):
        tolerance = 1e-7

        if self.battery_action == BatteryAction.IDLE:
            if abs(self.battery_kwh) > tolerance:
                raise ValueError(
                    "battery_kwh must be 0 when battery_action is idle"
                )

        elif self.battery_kwh <= tolerance:
            raise ValueError(
                "battery_kwh must be greater than 0 when charging or discharging"
            )

        return self


class OptimizeEnergyResponse(StrictBaseModel):
    scenario_id: str
    directive_interpretation: list[DirectiveInterpretation]
    hourly_plan: list[HourlyPlanItem]
    total_grid_kwh: float = Field(ge=0)
    total_cost_bdt: float = Field(ge=0)
    peak_grid_kwh: float = Field(ge=0)
    plan_summary: str = Field(min_length=1)

    @field_validator(
        "total_grid_kwh",
        "total_cost_bdt",
        "peak_grid_kwh",
    )
    @classmethod
    def validate_finite_totals(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("Response totals must be finite numbers")

        return value