"""Integration tests for OctaveBridge → NumEngine routing.

These tests verify that high-level Octave-style calls (``eig``, ``svd``,
``fft``, ``ifft``, ``polyfit``, ``inv``) are correctly routed by
``OctaveBridge`` to the underlying ``NumEngine`` and produce numerically
correct results. They span both modules and therefore are marked as
integration tests.

The ``bridge`` fixture is provided by the root conftest.
"""

import numpy as np
import pytest


@pytest.mark.integration
def test_eig(bridge):
    """eig() should route to NumEngine.eigenvalues and return a dict."""
    bridge.evaluate("M = [2 0; 0 3]")
    result = bridge.evaluate("eig(M)")
    assert "eigenvalues" in result
    evals = np.sort(np.real(result["eigenvalues"]))
    assert pytest.approx(evals[0], abs=1e-10) == 2.0
    assert pytest.approx(evals[1], abs=1e-10) == 3.0


@pytest.mark.integration
def test_svd(bridge):
    """svd() should route to NumEngine.svd; singular values are non-negative."""
    bridge.evaluate("M = [1 2; 3 4; 5 6]")
    result = bridge.evaluate("svd(M)")
    assert "S" in result
    assert np.all(result["S"] >= 0)


@pytest.mark.integration
def test_fft(bridge):
    """fft() should return the spectrum array of the same length as input."""
    result = bridge.evaluate("fft([1 0 -1 0])")
    assert result is not None
    assert len(result) == 4


@pytest.mark.integration
def test_ifft(bridge):
    """fft → ifft round-trip should recover the original signal."""
    bridge.evaluate("sig = [1.0 2.0 3.0 4.0]")
    bridge.evaluate("S = fft(sig)")
    recovered = bridge.evaluate("ifft(S)")
    np.testing.assert_array_almost_equal(
        np.array([1.0, 2.0, 3.0, 4.0]),
        recovered.real,
        decimal=10,
    )


@pytest.mark.integration
def test_polyfit(bridge):
    """polyfit should route to NumEngine.polynomial_fit and return coefficients."""
    bridge.evaluate("x = [1 2 3 4]")
    bridge.evaluate("y = [1 4 9 16]")
    coeffs = bridge.evaluate("polyfit(x, y, 2)")
    # y = x² → leading coefficient should be ~1
    assert pytest.approx(coeffs[0], abs=1e-6) == 1.0


@pytest.mark.integration
def test_inv(bridge):
    """inv() should return the correct inverse matrix via np.linalg.inv."""
    bridge.evaluate("A = [2 0; 0 4]")
    result = bridge.evaluate("inv(A)")
    expected = np.array([[0.5, 0.0], [0.0, 0.25]])
    np.testing.assert_array_almost_equal(result, expected)
