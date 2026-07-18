# Pollinator Go Principles

These principles capture the design values that recur across Pollinator Go's domain guidance. Use them to interpret rules, reconcile tensions, and recognize when several local preferences express one broader idea. Domain skills and references remain the source of executable guidance.

## Keep ownership clear

Give behavior, contracts, and lifecycle responsibilities one clear owner. Keep integration mechanics at the boundary that translates between owners.

## Keep contracts explicit

Make important contracts and transitions visible at their owning boundary, even when explicitness introduces a small amount of repetition.

## Define strong defaults

Choose one clear default before documenting variants. Preserve coherent local conventions where they do not undermine the intended boundary or contract.

## Make risky behavior deliberate

Prefer safe, repeatable behavior by default. Make destructive operations, mutable initialization, and compatibility-breaking changes explicit.
