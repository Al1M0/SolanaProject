"""Verify persisted values before packaging the original, unchanged research engine."""
import base64
from .domain import ResearchDataError
from .engine import digest
from .experiments import train_experiment, evaluate_experiment, bundle_zip


def same_values(actual, expected):
    # JSON.stringify loses Python's distinction between 1000.0 and 1000.
    # Accept that representation change only: no numeric tolerance or bool coercion.
    if type(actual) in (int, float) and type(expected) in (int, float):
        return actual == expected
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        return actual.keys() == expected.keys() and all(same_values(actual[k], expected[k]) for k in actual)
    if isinstance(actual, list):
        return len(actual) == len(expected) and all(same_values(a, b) for a, b in zip(actual, expected))
    return actual == expected


def verified_bundle_zip(dataset, manifest, trained, holdout=None, progress=None):
    expected = {**trained, "holdout": holdout}
    actual = train_experiment(dataset, manifest, progress)
    actual["holdout"] = evaluate_experiment(dataset, manifest, digest(manifest)) if holdout is not None else None
    if not same_values(actual, expected):
        raise ResearchDataError("Export verification failed: saved results differ from the exact frozen rerun. No bundle was produced.")
    # Fresh Python values preserve float/int encoding for the strict offline verifier.
    return bundle_zip(dataset, manifest, {k: actual[k] for k in ("training", "sensitivity")}, actual["holdout"])


def verified_bundle_base64(*args):
    return base64.b64encode(verified_bundle_zip(*args)).decode()
