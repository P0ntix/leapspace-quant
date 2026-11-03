"""Live end-to-end check: fetch a real option chain, compute gamma + flow."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from leapspace.market import fetch_option_chain, fetch_ohlcv
from leapspace.gamma import compute_gamma_exposure, compute_option_flow, merge_flow_and_gamma

sym = sys.argv[1] if len(sys.argv) > 1 else "QQQ"
try:
    chain, prov = fetch_option_chain(sym)
    print(f"CHAIN {sym}: {prov.disclosure()}")
    print(f"  spot={chain['spot']} as_of={chain['as_of']} expiries={len(chain['expirations'])}")
    print(f"  contracts={len(chain['contracts'])}")
    c0 = chain["contracts"][0]
    print(f"  sample contract: {c0}")

    g = compute_gamma_exposure(chain)
    print("\nGAMMA:")
    for k in ("net_gamma", "call_gamma", "put_gamma", "gross_gamma",
              "max_pain_strike", "zero_gamma_strike", "n_contracts",
              "total_oi", "total_volume"):
        print(f"  {k} = {getattr(g, k)}")
    print(f"  sign={g.sign} state={g.state}")
    print(f"  interpretation: {g.interpretation()}")
    print(f"  warnings: {g.warnings[:3]}")

    f = compute_option_flow(chain)
    print("\nFLOW:")
    for k in ("call_volume", "put_volume", "put_call_volume_ratio",
              "net_delta_flow", "net_vega_flow", "net_notional_flow",
              "directional_flow", "volume_implied"):
        print(f"  {k} = {getattr(f, k)}")

    m = merge_flow_and_gamma(f, g)
    print(f"\nCOMBINED state={m['combined_state']}")
except Exception as e:
    print("ERROR", type(e).__name__, e)
    raise
