"""
leapspace-quant — automation built from the seven LeapSpace research papers
supplied by the user.

Modules
-------
provenance  : every datum carries where it came from; synthetic data is labelled.
http        : stdlib HTTP with a browser UA, retries, gzip, disk cache.
regime      : Gaussian HMM regime identification (3-5 states) + the papers'
              momentum/reversal regime-switch policy.
market      : Yahoo OHLCV, options chains (open interest + volume), crypto.
gamma       : dealer gamma exposure and option-flow measures.
onchain     : Solana wallet tracking and transaction analysis.
disclosure  : US officials' legally-required financial disclosures — legislative,
              executive and judicial branches — plus market-impact analysis.
alerts      : price / information / action alerts driven by the papers.
backtest    : strategy specs + the validation gauntlet.
"""

__version__ = "1.0.0"
