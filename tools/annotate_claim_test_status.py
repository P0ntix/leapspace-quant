"""Annotate the claim inventory with the specs that ALREADY test each claim.

The C1-C8 matrix in `leapspace/paperspecs.py` is not the only place these
papers have been built. There is also a set of STANDALONE specs - the six
"LeapSpace 2.0" specs in `leapspace/data/leapspace_2_0_specs.json`, the
earlier `v1_*` specs, and the `REGIME_SWITCH_SPECS` in `leapspace/backtest.py` -
each of which has a verdict in `reports/*.md`.

A claim that was already tested and REFUTED is very different from a claim
that was never tested. This script writes that distinction into the Status
column of the inventory so a spec writer does not rebuild what has already
been refuted, and does not mistake a refuted result for an untested claim.

Run:  python tools/annotate_claim_test_status.py
"""
from __future__ import annotations

import os
import re

BODY = r"C:/Users/HP/AppData/Local/hermes/projects/leapspace-quant/reports/paper_claims_body.md"

# claim_id -> list of (spec name, verdict, universe)
ALSO_TESTED: dict[str, list[tuple[str, str, str]]] = {
    # --- LeapSpace 2.0 standalone specs -------------------------------------
    "RET-13": [("crypto_ma20_trend_momentum", "REFUTED", "crypto"),
               ("nasdaq_12m_timeseries_momentum", "SUPPORTED", "us_equity_style")],
    "RET-14": [("nasdaq_12m_timeseries_momentum", "SUPPORTED", "us_equity_style"),
               ("v1_nasdaq_12m_tsm_vol_scaled", "REFUTED", "us_equity_style"),
               ("crypto_ma20_trend_momentum", "REFUTED", "crypto"),
               ("v1_crypto_momentum_20d_ma", "FRAGILE", "crypto")],
    "RET-16": [("nasdaq_12m_timeseries_momentum", "SUPPORTED", "us_equity_style"),
               ("v1_nasdaq_12m_tsm_vol_scaled", "REFUTED", "us_equity_style")],
    "RET-17": [("nasdaq_12m_timeseries_momentum", "SUPPORTED", "us_equity_style"),
               ("v1_nasdaq_12m_tsm_vol_scaled", "REFUTED", "us_equity_style"),
               ("v1_crypto_momentum_20d_ma", "FRAGILE", "crypto")],
    "RET-18": [("nasdaq_12m_timeseries_momentum", "SUPPORTED", "us_equity_style"),
               ("crypto_ma20_trend_momentum", "REFUTED", "crypto")],
    "RET-19": [("nasdaq_12m_timeseries_momentum", "SUPPORTED", "us_equity_style")],
    "RET-20": [("nasdaq_12m_timeseries_momentum", "SUPPORTED", "us_equity_style")],
    "RET-21": [("crypto_ma20_trend_momentum", "REFUTED", "crypto"),
               ("nasdaq_12m_timeseries_momentum", "SUPPORTED", "us_equity_style"),
               ("v1_crypto_momentum_20d_ma", "FRAGILE", "crypto")],
    "RET-22": [("crypto_ma20_trend_momentum", "REFUTED", "crypto"),
               ("v1_crypto_momentum_20d_ma", "FRAGILE", "crypto")],
    "RET-23": [("crypto_ma20_trend_momentum", "REFUTED", "crypto"),
               ("v1_crypto_momentum_20d_ma", "FRAGILE", "crypto")],
    "RET-26": [("sd_band_mean_reversion_crypto", "REFUTED", "crypto")],
    "RET-27": [("sd_band_mean_reversion_crypto", "REFUTED", "crypto")],
    "RET-29": [("sd_band_mean_reversion_crypto", "REFUTED", "crypto")],
    "RET-39": [("crypto_xs_momentum_volume_confirmed", "REFUTED", "crypto")],
    "RET-40": [("crypto_xs_momentum_volume_confirmed", "REFUTED (declared but UNENFORCED)", "crypto")],
    "RET-42": [("crypto_xs_momentum_volume_confirmed", "REFUTED", "crypto")],
    "RET-45": [("crypto_xs_momentum_volume_confirmed", "REFUTED", "crypto")],
    "RET-73": [("sd_band_mean_reversion_crypto", "REFUTED", "crypto")],
    "RET-75": [("sd_band_mean_reversion_crypto", "REFUTED", "crypto")],
    "RET-78": [("sd_band_mean_reversion_crypto", "REFUTED", "crypto")],
    "RET-79": [("sd_band_mean_reversion_crypto", "REFUTED", "crypto"),
               ("v1_sd_band_mean_reversion_1_0_1_5", "REFUTED", "crypto")],
    "RET-80": [("v1_sd_band_mean_reversion_1_0_1_5", "REFUTED", "crypto")],
    "RET-81": [("v1_sd_band_mean_reversion_1_0_1_5", "REFUTED", "crypto")],
    "RET-82": [("sd_band_mean_reversion_crypto", "REFUTED", "crypto"),
               ("v1_sd_band_mean_reversion_1_0_1_5", "REFUTED", "crypto"),
               ("bollinger20_2_breakout_crypto", "REFUTED", "crypto")],
    "RET-84": [("bollinger20_2_breakout_crypto", "REFUTED", "crypto")],
    "RET-94": [("bollinger20_2_breakout_crypto", "REFUTED", "crypto")],
    "IND-01": [("tradingview_price_volume_rsi_regime_filtered", "REFUTED", "crypto+equity mix")],
    "IND-02": [("crypto_rsi_oversold_fade", "REFUTED", "crypto"),
               ("tradingview_price_volume_rsi_regime_filtered", "REFUTED", "crypto+equity mix")],
    "IND-04": [("tradingview_price_volume_rsi_regime_filtered", "REFUTED", "crypto+equity mix")],
    "IND-05": [("crypto_rsi_oversold_fade", "REFUTED", "crypto"),
               ("tradingview_price_volume_rsi_regime_filtered", "REFUTED", "crypto+equity mix")],
    "IND-06": [("tradingview_price_volume_rsi_regime_filtered", "REFUTED", "crypto+equity mix")],
    "IND-08": [("crypto_rsi_oversold_fade", "REFUTED", "crypto")],
    "IND-09": [("tradingview_price_volume_rsi_regime_filtered", "REFUTED", "crypto+equity mix"),
               ("regime_switch_cross_sectional_sector_rotation", "SUPPORTED", "us_equity_style")],
    "IND-11": [("tradingview_price_volume_rsi_regime_filtered", "REFUTED", "crypto+equity mix")],
    "REG-01": [("regime_switch_cross_sectional_sector_rotation", "SUPPORTED", "us_equity_style"),
               ("regime_switch_momentum_reversal_us_equity", "REFUTED", "us_equity"),
               ("regime_switch_momentum_reversal_nasdaq_scalp_proxy", "REFUTED", "us_equity_style")],
    "REG-02": [("regime_switch_cross_sectional_sector_rotation", "SUPPORTED", "us_equity_style")],
    "REG-09": [("regime_switch_cross_sectional_sector_rotation", "SUPPORTED", "us_equity_style")],
    "REG-10": [("regime_switch_cross_sectional_sector_rotation", "SUPPORTED", "us_equity_style")],
    "REG-11": [("regime_switch_momentum_reversal_us_equity", "REFUTED", "us_equity")],
    "REG-12": [("regime_switch_momentum_reversal_us_equity", "REFUTED", "us_equity")],
    "REG-14": [("regime_switch_cross_sectional_sector_rotation", "SUPPORTED", "us_equity_style")],
    "REG-15": [("regime_switch_cross_sectional_sector_rotation", "SUPPORTED", "us_equity_style")],
    "REG-16": [("regime_switch_cross_sectional_sector_rotation", "SUPPORTED", "us_equity_style"),
               ("regime_switch_momentum_reversal_us_equity", "REFUTED", "us_equity")],
    "REG-50": [("regime_switch_cross_sectional_sector_rotation", "SUPPORTED", "us_equity_style")],
    "REG-64": [("regime_switch_cross_sectional_sector_rotation", "SUPPORTED", "us_equity_style")],
    "REG-65": [("regime_switch_cross_sectional_sector_rotation", "SUPPORTED", "us_equity_style")],
    "NAS-16": [("regime_switch_momentum_reversal_nasdaq_scalp_proxy", "REFUTED", "us_equity_style")],
    "NAS-17": [("regime_switch_momentum_reversal_nasdaq_scalp_proxy", "REFUTED", "us_equity_style")],
    "NAS-19": [("regime_switch_momentum_reversal_nasdaq_scalp_proxy", "REFUTED", "us_equity_style")],
    "NAS-20": [("regime_switch_momentum_reversal_nasdaq_scalp_proxy", "REFUTED", "us_equity_style")],
}

MARK = " - ALSO TESTED: "


def main() -> None:
    txt = open(BODY, encoding="utf-8").read()
    out = []
    patched = 0
    for line in txt.splitlines():
        m = re.match(r"^(\|\s*)([A-Z]+-\d+)(\s*\|.*)$", line)
        if m and m.group(2) in ALSO_TESTED:
            cells = line.split("|")
            assert len(cells) == 10, (m.group(2), len(cells))  # 8 cells + 2 empties
            status = cells[5]
            assert MARK not in status, f"{m.group(2)} already annotated"
            specs = ALSO_TESTED[m.group(2)]
            tag = "; ".join(f"{n} [{u}] -> {v}" for n, v, u in specs)
            cells[5] = status.rstrip() + MARK + tag
            line = "|".join(cells)
            patched += 1
        out.append(line)
    assert patched == len(ALSO_TESTED), (patched, len(ALSO_TESTED))
    open(BODY, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"annotated {patched} claim rows with ALSO TESTED status")


if __name__ == "__main__":
    main()
