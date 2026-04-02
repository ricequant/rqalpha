import Mathlib.Algebra.BigOperators.Group.Finset
import Mathlib.Data.Rat.Basic

/-- A position is a quantity held at a price. -/
structure Position where
  qty : ℚ
  price : ℚ

/-- Portfolio value is the dot product of quantities and prices. -/
def portfolioValue (ps : List Position) : ℚ :=
  ps.foldl (fun acc p => acc + p.qty * p.price) 0

/-- An empty portfolio has zero value. -/
theorem empty_portfolio_zero : portfolioValue [] = 0 := rfl

/-- Adding a zero-quantity position doesn't change portfolio value. -/
theorem zero_position_identity (ps : List Position) (p : ℚ) :
    portfolioValue (ps ++ [⟨0, p⟩]) = portfolioValue ps := by
  simp [portfolioValue, List.foldl_append, mul_comm, zero_mul]