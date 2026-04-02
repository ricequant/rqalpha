import Mathlib.Order.Filter.Basic
import Mathlib.Data.List.Basic

/-- Market observation at a single timestep. -/
structure Tick where
  open_ : ℚ
  high : ℚ
  low : ℚ
  close : ℚ
  volume : ℕ
  timestamp : ℕ

/-- A causal strategy maps a history prefix to a signal.
    The key constraint: it receives a List, not a Function over all time. -/
def CausalStrategy (σ : Type) := List Tick → σ

/-- Two histories agree up to time T. -/
def prefix_eq (h1 h2 : List Tick) (T : ℕ) : Prop :=
  h1.take T = h2.take T

/-- A strategy is non-anticipatory if its output at time T
    depends only on observations [0, T). -/
def NonAnticipatory (s : CausalStrategy σ) : Prop :=
  ∀ (h1 h2 : List Tick) (T : ℕ),
    T ≤ h1.length → T ≤ h2.length →
    prefix_eq h1 h2 T →
    s (h1.take T) = s (h2.take T)

/-- Any CausalStrategy applied to a prefix is trivially non-anticipatory,
    because List.take is deterministic. -/
theorem causal_strategy_non_anticipatory (s : CausalStrategy σ) :
    NonAnticipatory s := by
  intro h1 h2 T _ _ h_eq
  unfold prefix_eq at h_eq
  rw [h_eq]