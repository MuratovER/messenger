import typing

from factory.builder import BuildStep
from factory.faker import Faker


class UniqueFaker(Faker):
    def evaluate(
        self, instance: typing.Any, step: BuildStep, extra: typing.Any
    ) -> Faker:
        extra = {"locale": "en_US"}
        value = super().evaluate(instance, step, extra)
        return value


class UniqueStringFaker(UniqueFaker):
    def evaluate(self, instance: typing.Any, step: BuildStep, extra: typing.Any) -> str:  # type: ignore
        value = super().evaluate(instance, step, extra)
        return f"{step.sequence}_{value}"
