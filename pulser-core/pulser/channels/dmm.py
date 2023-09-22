# Copyright 2023 Pulser Development Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Defines the detuning map modulator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

import numpy as np

from pulser.channels.base_channel import Channel
from pulser.pulse import Pulse


@dataclass(init=True, repr=False, frozen=True)
class DMM(Channel):
    """Defines a Detuning Map Modulator (DMM) Channel.

    A Detuning Map Modulator can be used to define `Global` detuning Pulses
    (of zero amplitude and phase). These Pulses are locally modulated by the
    weights of a `DetuningMap`, thus providing a local control over the
    detuning. The detuning of the pulses added to a DMM has to be negative,
    between 0 and `bottom_detuning`. Channel targeting the transition between
    the ground and rydberg states, thus encoding the 'ground-rydberg' basis.

    Note:
        The protocol to add pulses to the DMM Channel is by default
        "no-delay".

    Args:
        bottom_detuning: Minimum possible detuning (in rad/µs), must be below
            zero.
        clock_period: The duration of a clock cycle (in ns). The duration of a
            pulse or delay instruction is enforced to be a multiple of the
            clock cycle.
        min_duration: The shortest duration an instruction can take.
        max_duration: The longest duration an instruction can take.
        min_avg_amp: The minimum average amplitude of a pulse (when not zero).
        mod_bandwidth: The modulation bandwidth at -3dB (50% reduction), in
            MHz.
    """

    bottom_detuning: Optional[float] = field(default=None, init=True)
    addressing: Literal["Global"] = field(default="Global", init=False)
    max_abs_detuning: Optional[float] = field(default=None, init=False)
    max_amp: float = field(default=0, init=False)
    min_retarget_interval: Optional[int] = field(default=None, init=False)
    fixed_retarget_t: Optional[int] = field(default=None, init=False)
    max_targets: Optional[int] = field(default=None, init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.bottom_detuning and self.bottom_detuning > 0:
            raise ValueError("bottom_detuning must be negative.")

    @property
    def basis(self) -> Literal["ground-rydberg"]:
        """The addressed basis name."""
        return "ground-rydberg"

    def _undefined_fields(self) -> list[str]:
        optional = [
            "bottom_detuning",
            "max_duration",
        ]
        return [field for field in optional if getattr(self, field) is None]

    def validate_pulse(self, pulse: Pulse) -> None:
        """Checks if a pulse can be executed in this DMM.

        Args:
            pulse: The pulse to validate.
        """
        super().validate_pulse(pulse)
        round_detuning = np.round(pulse.detuning.samples, decimals=6)
        if np.any(round_detuning > 0):
            raise ValueError("The detuning in a DMM must not be positive.")
        if self.bottom_detuning is not None and np.any(
            round_detuning < self.bottom_detuning
        ):
            raise ValueError(
                "The detuning goes below the bottom detuning "
                f"of the DMM ({self.bottom_detuning} rad/µs)."
            )


def _dmm_id_from_name(dmm_name: str) -> str:
    """Converts a dmm_name into a dmm_id.

    As a reminder the dmm_name is generated automatically from dmm_id
    as dmm_id_{number of times dmm_id has been called}.

    Args:
        dmm_name: The dmm_name to convert.

    Returns:
        The associated dmm_id.
    """
    return "_".join(dmm_name.split("_")[0:2])


def _get_dmm_name(dmm_id: str, channels: list[str]) -> str:
    """Get the dmm_name to add a dmm_id to a list of channels.

    Counts the number of channels starting by dmm_id, generates the
    dmm_name as dmm_id_{number of times dmm_id has been called}.

    Args:
        dmm_id: the id of the DMM to add to the list of channels.
        channels: a list of channel names.

    Returns:
        The associated dmm_name.
    """
    dmm_count = len(
        [key for key in channels if _dmm_id_from_name(key) == dmm_id]
    )
    if dmm_count == 0:
        return dmm_id
    return dmm_id + f"_{dmm_count}"
