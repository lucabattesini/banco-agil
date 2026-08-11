from typing import Annotated

from pydantic import Field

CpfField = Annotated[str, Field(pattern=r"^\d{11}$", description="Digits only, no dots or dashes.")]
BirthDateField = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="Format: YYYY-MM-DD.")]
PositiveAmountField = Annotated[float, Field(gt=0, description="Plain number in BRL, greater than zero.")]
NonNegativeAmountField = Annotated[float, Field(ge=0, description="Plain number in BRL, zero or greater.")]
DependentsField = Annotated[int, Field(ge=0, description="Number of dependents, zero or greater.")]
