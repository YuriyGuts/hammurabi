"""Answer verifiers for checking solution output."""

from __future__ import annotations

from hammurabi.grader.verifiers.common import AnswerVerifier
from hammurabi.grader.verifiers.common import FloatSequenceVerifier
from hammurabi.grader.verifiers.common import IntegerSequenceVerifier
from hammurabi.grader.verifiers.common import SpaceCharacterSeparatedSequenceVerifier
from hammurabi.grader.verifiers.common import WordSequenceVerifier
from hammurabi.grader.verifiers.custom import MyCustomVerifier

__all__ = [
    "AnswerVerifier",
    "FloatSequenceVerifier",
    "IntegerSequenceVerifier",
    "SpaceCharacterSeparatedSequenceVerifier",
    "WordSequenceVerifier",
    "MyCustomVerifier",
    "registered_verifiers",
]

# Registry mapping verifier names to classes
registered_verifiers: dict[str, type[AnswerVerifier]] = {
    "AnswerVerifier": AnswerVerifier,
    "FloatSequenceVerifier": FloatSequenceVerifier,
    "IntegerSequenceVerifier": IntegerSequenceVerifier,
    "SpaceCharacterSeparatedSequenceVerifier": SpaceCharacterSeparatedSequenceVerifier,
    "WordSequenceVerifier": WordSequenceVerifier,
    "MyCustomVerifier": MyCustomVerifier,
}
