# TECHNICAL FUNCTION REFERENCE — leapspace-quant

**Generated from the code** by `tools/build_function_reference.py`. A hand-written function reference is wrong the moment the code changes, and wrong in a way nobody notices. This one is read out of the source with `ast`, so it cannot drift.

**Measured:** 63 modules, 42,166 lines, 422 public functions, 59 classes.

**The gotchas are curated, not derived.** A gotcha is a piece of knowledge that is not *in* the code - it is what the code does NOT say. Those entries are written by hand; everything else is read out of the source.

---

## Contents


### Infrastructure

| Module | Lines | Public fns | Classes | Depends on |
|---|---|---|---|---|
| [`adapter_checks`](#adapter_checks) | 331 | 4 | 2 | `provenance` |
| [`archviz`](#archviz) | 450 | 3 | 0 | — |
| [`cli`](#cli) | 698 | 12 | 0 | `alerts`, `archviz`, `backtest`, `disclosure`, `gamma`, +8 |
| [`cmd_extra`](#cmd_extra) | 580 | 9 | 0 | `edge`, `holders`, `launchscan`, `market`, `memecoinscan`, +4 |
| [`http`](#http) | 269 | 6 | 2 | `provenance` |
| [`models`](#models) | 421 | 3 | 12 | `provenance` |
| [`provenance`](#provenance) | 136 | 4 | 3 | — |
| [`reportvalidate`](#reportvalidate) | 518 | 2 | 0 | `adapter_checks` |
| [`socialedge`](#socialedge) | 1375 | 16 | 0 | `http` |

### Data sources

| Module | Lines | Public fns | Classes | Depends on |
|---|---|---|---|---|
| [`chainregistry`](#chainregistry) | 261 | 8 | 0 | `http`, `provenance` |
| [`chains`](#chains) | 784 | 6 | 2 | `http`, `models`, `provenance` |
| [`crosschain`](#crosschain) | 1234 | 11 | 0 | `costs`, `http`, `provenance` |
| [`deployers`](#deployers) | 398 | 5 | 0 | `chains`, `http`, `models`, `provenance` |
| [`disclosure`](#disclosure) | 1047 | 14 | 5 | `http`, `provenance` |
| [`etherscan`](#etherscan) | 300 | 10 | 0 | `http` |
| [`holders`](#holders) | 555 | 12 | 0 | `http`, `memecoin`, `provenance` |
| [`market`](#market) | 403 | 10 | 0 | `http`, `provenance` |
| [`narrative`](#narrative) | 555 | 7 | 0 | `provenance` |
| [`onchain`](#onchain) | 571 | 10 | 2 | `http`, `provenance` |
| [`priceatblock`](#priceatblock) | 328 | 6 | 0 | `costs` |
| [`priced`](#priced) | 396 | 7 | 1 | `costs`, `edge`, `http`, `memecoinscan`, `priceatblock` |
| [`social`](#social) | 866 | 6 | 0 | `chains`, `http`, `memecoin`, `provenance` |
| [`source_reliability`](#source_reliability) | 81 | 4 | 0 | — |
| [`traders`](#traders) | 601 | 11 | 0 | `chains`, `provenance`, `stats` |
| [`whitelist`](#whitelist) | 282 | 4 | 0 | `provenance` |

### Features & leading indicators

| Module | Lines | Public fns | Classes | Depends on |
|---|---|---|---|---|
| [`cryptoderivs`](#cryptoderivs) | 482 | 9 | 0 | `http`, `leading`, `provenance` |
| [`gamma`](#gamma) | 521 | 8 | 2 | `stats` |
| [`leading`](#leading) | 711 | 9 | 0 | `gamma`, `http`, `market`, `provenance` |
| [`leadingcache`](#leadingcache) | 255 | 6 | 0 | `leading`, `provenance` |
| [`leadingspecs`](#leadingspecs) | 318 | 2 | 0 | — |
| [`regime`](#regime) | 586 | 3 | 2 | — |

### Signals

| Module | Lines | Public fns | Classes | Depends on |
|---|---|---|---|---|
| [`ensemble`](#ensemble) | 415 | 2 | 0 | `paperspecs` |
| [`stats`](#stats) | 194 | 7 | 0 | — |
| [`trend`](#trend) | 344 | 4 | 0 | `backtest` |

### Portfolio & risk

| Module | Lines | Public fns | Classes | Depends on |
|---|---|---|---|---|
| [`costs`](#costs) | 1416 | 14 | 1 | `http`, `provenance` |
| [`friction`](#friction) | 1401 | 2 | 14 | `models`, `provenance` |
| [`portfolio`](#portfolio) | 612 | 7 | 0 | — |
| [`riskguard`](#riskguard) | 798 | 3 | 3 | `models`, `provenance` |

### Backtest engine

| Module | Lines | Public fns | Classes | Depends on |
|---|---|---|---|---|
| [`backtest`](#backtest) | 2291 | 6 | 1 | `ensemble`, `leading`, `leadingcache`, `provenance`, `regime`, +2 |
| [`paperrun`](#paperrun) | 409 | 3 | 0 | `backtest`, `leading`, `leadingcache` |
| [`paperspecs`](#paperspecs) | 808 | 4 | 0 | `ensemble` |
| [`quant`](#quant) | 1370 | 17 | 0 | `backtest`, `biasaudit`, `chainregistry`, `chains`, `cmd_extra`, +16 |
| [`specs_2_0`](#specs_2_0) | 62 | 2 | 0 | — |

### Validation

| Module | Lines | Public fns | Classes | Depends on |
|---|---|---|---|---|
| [`biasaudit`](#biasaudit) | 832 | 4 | 0 | `backtest`, `models` |
| [`criteria`](#criteria) | 139 | 10 | 0 | — |
| [`edge`](#edge) | 948 | 9 | 0 | `gate_tests`, `pbo`, `stats`, `traders` |
| [`gate_tests`](#gate_tests) | 286 | 1 | 1 | `pbo` |
| [`pbo`](#pbo) | 718 | 5 | 0 | — |
| [`reference_gate`](#reference_gate) | 1105 | 9 | 0 | — |

### Reports & visualisation

| Module | Lines | Public fns | Classes | Depends on |
|---|---|---|---|---|
| [`backtestviz`](#backtestviz) | 899 | 4 | 0 | `viz_leading` |
| [`paperreport`](#paperreport) | 953 | 5 | 0 | `viz_leading` |
| [`report`](#report) | 396 | 3 | 0 | `provenance`, `reportvalidate`, `source_reliability` |
| [`report_memecoin`](#report_memecoin) | 2508 | 4 | 0 | `etherscan` |
| [`viz`](#viz) | 789 | 10 | 0 | `backtest`, `chains`, `friction`, `models`, `report`, +1 |
| [`viz_leading`](#viz_leading) | 474 | 4 | 0 | — |
| [`viz_memecoin`](#viz_memecoin) | 346 | 5 | 0 | `viz` |

### Governance & policy

| Module | Lines | Public fns | Classes | Depends on |
|---|---|---|---|---|
| [`alerts`](#alerts) | 753 | 7 | 2 | `provenance` |
| [`signal`](#signal) | 1269 | 14 | 2 | `riskguard` |

### Wallet & chain profiling

| Module | Lines | Public fns | Classes | Depends on |
|---|---|---|---|---|
| [`launchscan`](#launchscan) | 628 | 7 | 0 | `costs`, `edge`, `http`, `memecoinscan`, `provenance` |
| [`memecoin`](#memecoin) | 779 | 5 | 1 | `http`, `market`, `narrative`, `provenance` |
| [`memecoinscan`](#memecoinscan) | 771 | 5 | 0 | `etherscan`, `http`, `provenance` |
| [`profiler`](#profiler) | 680 | 6 | 1 | `chains`, `models`, `provenance` |
| [`walletsearch`](#walletsearch) | 460 | 7 | 0 | — |

---

## The modules

# Infrastructure

_HTTP, caching, provenance, secrets, shared models_

<a id="adapter_checks"></a>
## `adapter_checks.py`

Adapter over the vendored `data_quality_checker` skill.

*331 lines · 4 public functions · 2 classes · layer: Infrastructure*

**Depends on:** `provenance`

**Module constants:**

```python
VENDOR_REL_PATH = 'leapspace/vendor/data_quality_checker'
VENDOR_CHECK_NAMES = ('price_scale', 'notation', 'dates', 'allocations', 'units')
```

**Functions**

```python
def vendor_available(package_root: Optional[str]=None) -> bool
def run_vendor_checks(content: str, checks: Optional[Sequence[str]]=None, as_of: Optional[date]=None, filepath: Optional[str]=None, package_root: Optional[str]=None) -> List[VendorFinding]
def check_token_activity(content: str, report_location: Optional[str]=None, tags: Optional[List[str]]=None, skip_checks: Optional[List[str]]=None, as_of: Optional[date]=None, package_root: Optional[str]=None) -> Dict[str, Any]
def main() -> int
```

- `vendor_available` — True when the vendored checker can be imported.
- `run_vendor_checks` — Run the vendored checks over ``content``.
- `check_token_activity` — Audit a generated research document for data-quality defects.
- `main` — Audit every generated markdown report in ``reports/``.

**Classes**

### `class AdapterUnavailable(RuntimeError)`

Raised when the vendored checker cannot be imported.

### `class VendorFinding`

One finding from the vendored checker, in this package's shape.

```python
def to_dict(self) -> Dict[str, Any]
```


---

<a id="archviz"></a>
## `archviz.py`

The architecture diagram: the project's flow, drawn.

*450 lines · 3 public functions · 0 classes · layer: Infrastructure*

**Module constants:**

```python
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, 'leapspace')
OUT_HTML = os.path.join(ROOT, 'reports', 'charts', 'architecture.html')
```

**Functions**

```python
def module_inventory() -> Dict[str, Any]
def render_architecture(mods: Optional[Dict[str, Dict[str, Any]]]=None) -> str
def build_architecture(out_path: Optional[str]=None) -> Dict[str, Any]
```

- `module_inventory` — Read the real shape of the package: modules, sizes, APIs, edges.
- `render_architecture` — Render the architecture page.
- `build_architecture` — Generate the architecture page.

---

<a id="cli"></a>
## `cli.py`

Command-line orchestrator.

*698 lines · 12 public functions · 0 classes · layer: Infrastructure*

**Depends on:** `alerts`, `archviz`, `backtest`, `disclosure`, `gamma`, `http`, `market`, `memecoin`, `onchain`, `provenance`, `quant`, `regime`, `report`

**Module constants:**

```python
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
DATA_DIR = os.path.join(PROJECT, 'data')
REPORT_DIR = os.path.join(PROJECT, 'reports')
STATE_DIR = os.path.join(PROJECT, 'state')
DEFAULT_SYMBOL = 'QQQ'
DEFAULT_GAMMA_SYMBOL = 'QQQ'
```

**Functions**

```python
def cmd_architecture(args) -> int
def cmd_regime(args) -> int
def cmd_gamma(args) -> int
def cmd_memes(args) -> int
def cmd_wallet(args) -> int
def cmd_disclosure(args) -> int
def cmd_alerts(args) -> int
def merge_backtest_results(path: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]
def cmd_backtest(args) -> int
def cmd_report(args) -> int
def build_parser() -> argparse.ArgumentParser
def main(argv: Optional[Sequence[str]]=None) -> int
```

- `cmd_architecture` — Generate the architecture diagram from the code.
- `merge_backtest_results` — Merge freshly-run rows INTO the stored results file and write it back.

---

<a id="cmd_extra"></a>
## `cmd_extra.py`

CLI command bodies that live outside quant.py.

*580 lines · 9 public functions · 0 classes · layer: Infrastructure*

**Depends on:** `edge`, `holders`, `launchscan`, `market`, `memecoinscan`, `report_memecoin`, `signal`, `traders`, `whitelist`

**Functions**

```python
def cmd_holders(args) -> int
def cmd_memeflow(args) -> int
def cmd_traders(args) -> int
def cmd_edge(args) -> int
def cmd_whitelist(args) -> int
def cmd_launchscan(args) -> int
def cmd_etherscan(args) -> int
def cmd_vizmem(args) -> int
def cmd_signal(args) -> int
```

- `cmd_holders` — Holder composition over time, and abrupt ownership changes.
- `cmd_memeflow` — Top holders of a memecoin, classified, with their allocation.
- `cmd_traders` — Wallet qualification against the cited standards.
- `cmd_edge` — Evaluate a wallet's edge against the fluke tests.
- `cmd_whitelist` — The whitelist of consistent traders, with rejected candidates shown.
- `cmd_launchscan` — Find the early buyers of a freshly launched meme and test them.
- `cmd_etherscan` — Etherscan V2: the one source that needs a key.
- `cmd_vizmem` — Build the memecoin-trader charts from the real artefacts.
- `cmd_signal` — Produce a decision-ready trade brief for one token.

---

<a id="http"></a>
## `http.py`

Stdlib HTTP layer with a browser User-Agent, retries, gzip handling and an
optional on-disk cache.

*269 lines · 6 public functions · 2 classes · layer: Infrastructure*

**Depends on:** `provenance`

**Module constants:**

```python
BROWSER_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, 
DEFAULT_HEADERS = {'User-Agent': BROWSER_UA, 'Accept': 'application/json,text/plain,*/*'
_SECRET_NAMES = ('ETHERSCAN_API_KEY', 'ETHERSCAN_KEY', 'MORALIS_API_KEY', 'ANTHROPIC_A
_SECRET_PATTERN = re.compile('(?i)\\b(?:apikey|api[_-]?key|apikey=)[\\s:=]*[A-Za-z0-9_\\
```

**Functions**

```python
def ssl_context() -> ssl.SSLContext
def http_get(url: str, headers: Optional[Dict[str, str]]=None, timeout: int=30, retries: int=3, backoff: float=1.5) -> Tuple[int, bytes, Dict[str, str]]
def http_json(url: str, headers: Optional[Dict[str, str]]=None, timeout: int=30, retries: int=3) -> Tuple[Any, int]
def http_post_json(url: str, payload: Any, headers: Optional[Dict[str, str]]=None, timeout: int=30, retries: int=3) -> Tuple[Any, int]
def get_secret(name: str) -> Optional[str]
def redact(text: str) -> str
```

- `http_get` — GET with retries. Raises HttpError (a SourceUnavailable) on failure.
- `get_secret` — A credential, or None. The value is returned to the caller only;
- `redact` — Strip credential-shaped strings out of text before it is written

**Classes**

### `class HttpError(SourceUnavailable)`

### `class CachedFetcher`

Fetch-with-cache helper.

```python
def get_json(self, name: str, url: str, params: Optional[Dict[str, Any]]=None, headers: Optional[Dict[str, str]]=None, max_age_seconds: Optional[float]=None, refresh: bool=False, timeout: int=30, source: str='http') -> Tuple[Any, Provenance]
```


> **Gotcha.** The SYSTEM CA store mis-validates Let's Encrypt chains on this host, so `ssl.create_default_context()` fails. `requests` and `certifi` work. The SSL context is built once from certifi.

---

<a id="models"></a>
## `models.py`

Unified on-chain models for the memecoin quant layer.

*421 lines · 3 public functions · 12 classes · layer: Infrastructure*

**Depends on:** `provenance`

**Module constants:**

```python
FAMILY_SVM = 'svm'
FAMILY_EVM = 'evm'
SUPPORTED_CHAINS = list(CHAINS.keys())
EVENT_TOKEN_CREATED = 'token_created'
EVENT_LIQUIDITY_ADDED = 'liquidity_added'
EVENT_WALLET_TRADE = 'wallet_trade'
EVENT_PRICE_UPDATE = 'price_update'
EVENT_LIQUIDITY_REMOVED = 'liquidity_removed'
EVENT_RUG_SIGNAL = 'rug_signal'
EVENT_KINDS = (EVENT_TOKEN_CREATED, EVENT_LIQUIDITY_ADDED, EVENT_WALLET_TRADE, EVENT
```

**Functions**

```python
def get_chain(chain_id: str) -> ChainSpec
def now_ts() -> int
def to_json(obj: Any) -> str
```

- `get_chain` — Look up a chain, with a helpful error rather than a KeyError.
- `to_json` — Serialise any model to its FLAT json form.

**Classes**

### `class ChainSpec`

Static facts about one chain. No network state.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class TokenEvent`

A unified on-chain event, normalised across chains.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class WalletTrade`

One wallet's trade in one token, normalised across chains.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class WalletProfile`

A wallet scored against the operator's consistency thresholds.

```python
def qualifies(self) -> bool
def to_flat(self) -> Dict[str, Any]
```


### `class FundingSource`

Where a wallet's first token arrived from — the anti-insider input.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class TokenCandidate`

A token that tripped a detection rule, with its traction evidence.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class Friction`

Execution friction assumptions. Every field is explicit and tunable.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class Position`

```python
def to_flat(self) -> Dict[str, Any]
```


### `class CopyTrade`

One simulated copy-trade, including the ones that were SKIPPED.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class KillSwitchState`

Whether trading is permitted, and why.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class Anomaly`

An unexpected market condition, logged with its exact context.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class BiasFinding`

One bias detected by the auditor.

```python
def to_flat(self) -> Dict[str, Any]
```


> **Gotcha.** The shared dataclasses. A field that was not measured is `None`, never `0` - a zero means something different from a missing value and the difference has caused silent wrong numbers.

---

<a id="provenance"></a>
## `provenance.py`

Provenance and disclosure primitives.

*136 lines · 4 public functions · 3 classes · layer: Infrastructure*

**Module constants:**

```python
LIVE = 'LIVE'
CACHE = 'CACHE'
SYNTHETIC = 'SYNTHETIC'
SYNTHETIC_DISCLOSURE = 'SYNTHETIC DATA — generated by leapspace.selftest / synthetic fixtures
```

**Functions**

```python
def utcnow_iso() -> str
def unavailable(source: str, url: Optional[str], reason: str) -> Dict[str, Any]
def write_json(path: str, payload: Any) -> str
def read_json(path: str, default: Any=None) -> Any
```

- `write_json` — Atomic JSON write (write to .tmp then os.replace).

**Classes**

### `class Provenance`

Where a piece of data came from, and whether it is real.

```python
def is_real(self) -> bool
def is_synthetic(self) -> bool
def disclosure(self) -> str
def to_dict(self) -> Dict[str, Any]
```


### `class DataPoint`

A value plus its provenance. Use .value; never lose the provenance.

```python
def is_real(self) -> bool
def is_synthetic(self) -> bool
```


### `class SourceUnavailable(Exception)`

Raised when a required source cannot be reached.

> **Gotcha.** The single chokepoint for credential redaction. Every fetch records its URL, HTTP status and what was measured, and every credential-shaped string is stripped before it reaches an artefact.

---

<a id="reportvalidate"></a>
## `reportvalidate.py`

Pre-flight report validator — a REAL gate over generated reports.

*518 lines · 2 public functions · 0 classes · layer: Infrastructure*

**Depends on:** `adapter_checks`

**Module constants:**

```python
VENDOR_CHECK_NAMES = ('price_scale', 'notation', 'dates', 'allocations', 'units')
ADAPTER_CHECK_NAMES = ('base_unit_scale', 'missing_not_zero', 'percent_scale')
BLOCKING_SEVERITIES = frozenset({'ERROR'})
ERC20_DECIMALS = 18
MISSING_TOKENS = ('n/a', 'unavailable', 'unknown', 'not available')
_RAW_BASE_UNIT = re.compile('(?<![\\d.$])\\d{16,}(?![\\d.])')
_MICRO_PRICE = re.compile('\\d\\.\\d+e-\\d+', re.IGNORECASE)
_PERCENT_100 = re.compile('(?<![\\d.])(\\d{1,3}(?:\\.\\d+)?)\\s*%')
_FRACTION_01 = re.compile('(?<![\\d.$])(0\\.\\d{2,})(?![\\d%])')
_FRAC_THEN_PAREN_PCT = re.compile('(?<![\\d.$])(0\\.\\d{2,})(?![\\d%])\\s*\\([^)\\n]{0,80}?(?
```

**Functions**

```python
def validate_report(markdown_text: str, payload: Optional[Dict[str, Any]]=None, *, checks: Optional[Sequence[str]]=None, as_of: Optional[Any]=None, filepath: Optional[str]=None) -> Dict[str, Any]
def format_validation_block(result: Dict[str, Any]) -> str
```

- `validate_report` — Validate a rendered report against the vendored + adapter checks.
- `format_validation_block` — Render a machine-readable validation warning block for a report.

> **Gotcha.** The pre-flight report validator. It finds known defect classes; it does NOT claim a report is correct. A clean result means only that the implemented checks found nothing.

---

<a id="socialedge"></a>
## `socialedge.py`

Social-edge testing: did this wallet buy BEFORE the crowd noticed?

*1375 lines · 16 public functions · 0 classes · layer: Infrastructure*

**Depends on:** `http`

**Module constants:**

```python
NARRATIVE_ESTABLISHED_MEMBERS_DEFAULT = 1000
MEMBERSHIP_THRESHOLD_DEFAULT = 500
COINCIDENT_WINDOW_HOURS_DEFAULT = 6.0
MIN_SNAPSHOTS_FOR_CROSSING = 2
HOLDER_GROWTH_INFLECTION_MULTIPLE = 2.0
MAJOR_MENTION_MULTIPLE = 3.0
MIN_MENTION_OBSERVATIONS = 4
MIN_DIVERGENCE_POINTS = 4
SOCIAL_SERIES_DIR = os.path.join(os.path.dirname(__file__), 'state', 'social_series')
LEADING = 'LEADING'
COINCIDENT = 'COINCIDENT'
LAGGING = 'LAGGING'
# ... and 8 more
```

**Functions**

```python
def build_community_series(snapshots: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]
def community_series_diagnostics(series: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def load_community_series(chain: str, mint: str) -> Dict[str, Any]
def save_community_series(chain: str, mint: str, snapshots: Sequence[Dict[str, Any]]) -> str
def record_community_snapshot(chain: str, mint: str, telegram_members: Optional[int]=None, discord_members: Optional[int]=None, telegram_online: Optional[int]=None, discord_online: Optional[int]=None, source: str='') -> Dict[str, Any]
def membership_threshold_event(series: Sequence[Dict[str, Any]], threshold: int=MEMBERSHIP_THRESHOLD_DEFAULT, platform: str='combined') -> Dict[str, Any]
def holder_inflection_event(holder_series: Sequence[Dict[str, Any]], multiple: float=HOLDER_GROWTH_INFLECTION_MULTIPLE) -> Dict[str, Any]
def first_mention_event(mention_series: Sequence[Dict[str, Any]], multiple: float=MAJOR_MENTION_MULTIPLE, count_key: str='mentions') -> Dict[str, Any]
def compute_lead_time(buy_ts: int, comparators: Dict[str, Dict[str, Any]], coincident_window_hours: float=COINCIDENT_WINDOW_HOURS_DEFAULT) -> Dict[str, Any]
def assess_wallet_edge(wallet_buys: Sequence[Dict[str, Any]], community_series: Sequence[Dict[str, Any]], token_address: Optional[str]=None, symbol: Optional[str]=None, holder_series: Optional[Sequence[Dict[str, Any]]]=None, mention_series: Optional[Sequence[Dict[str, Any]]]=None, membership_threshold: int=MEMBERSHIP_THRESHOLD_DEFAULT, coincident_window_hours: float=COINCIDENT_WINDOW_HOURS_DEFAULT) -> Dict[str, Any]
def narrative_established_ts(community_series: Sequence[Dict[str, Any]], threshold: int=NARRATIVE_ESTABLISHED_MEMBERS_DEFAULT) -> Dict[str, Any]
def classify_late_buyers(wallet_buys: Sequence[Dict[str, Any]], community_series: Sequence[Dict[str, Any]], token_address: Optional[str]=None, symbol: Optional[str]=None, established_threshold: int=NARRATIVE_ESTABLISHED_MEMBERS_DEFAULT, grace_hours: float=0.0) -> Dict[str, Any]
def social_vs_onchain_divergence(points: Sequence[Dict[str, Any]], social_key: str='combined_members', volume_key: str='volume', min_points: int=MIN_DIVERGENCE_POINTS, slope_window: Optional[int]=None) -> Dict[str, Any]
def telegram_post_activity(url: str, timeout: int=25) -> Dict[str, Any]
def build_activity_series(stamps: Sequence[int], bucket_seconds: int=3600) -> List[Dict[str, Any]]
def sample_community_size(social_links: Dict[str, str], timeout: int=25) -> Dict[str, Any]
```

- `build_community_series` — Turn raw snapshot records into a clean community-size time series.
- `community_series_diagnostics` — Describe the coverage of a community series, honestly.
- `load_community_series` — Load the stored community-size series for a token.
- `save_community_series` — Persist a community-size series. Atomic replace.
- `record_community_snapshot` — Append one timestamped community-size observation to the series.
- `membership_threshold_event` — The first snapshot at which community size crosses `threshold`.
- `holder_inflection_event` — The timestamp at which the holder-count growth rate inflects.
- `first_mention_event` — The first MAJOR social mention event in an attention series.
- `compute_lead_time` — Compute lead time in hours against each comparator.
- `assess_wallet_edge` — Full social-edge assessment for one wallet against one token.
- `narrative_established_ts` — The moment the narrative was ESTABLISHED, not merely detected.
- `classify_late_buyers` — Separate wallets that bought AFTER the narrative was established.
- `social_vs_onchain_divergence` — Flag the window where social is still RISING but volume has FALLEN.
- `telegram_post_activity` — Read the post timestamps from a Telegram channel's public preview.
- `build_activity_series` — Bucket post timestamps into a per-bucket POST COUNT series.
- `sample_community_size` — Read the CURRENT community size for a token's Telegram/Discord links.

---

# Data sources

_Market, on-chain, social, disclosure, macro data_

<a id="chainregistry"></a>
## `chainregistry.py`

The multi-chain memecoin registry.

*261 lines · 8 public functions · 0 classes · layer: Data sources*

**Depends on:** `http`, `provenance`

**Module constants:**

```python
REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'chai
MEME_SYMBOL_HINTS = ('PEPE', 'DOGE', 'SHIB', 'BONK', 'WIF', 'FLOKI', 'BRETT', 'MOG', 'POPC
```

**Functions**

```python
def load_registry(path: Optional[str]=None) -> Dict[str, Any]
def chains(path: Optional[str]=None) -> List[Dict[str, Any]]
def chain(chain_id: str, path: Optional[str]=None) -> Optional[Dict[str, Any]]
def top_chains(n: int=10, path: Optional[str]=None) -> List[Dict[str, Any]]
def layer_split(path: Optional[str]=None) -> Dict[str, List[Dict[str, Any]]]
def screenable_chains(path: Optional[str]=None) -> List[Dict[str, Any]]
def chain_health(path: Optional[str]=None) -> Dict[str, Any]
def discover_memecoins(chain_id: str, limit: int=20, pages: int=2, meme_only: bool=True) -> Dict[str, Any]
```

- `chains` — All registered chains, in rank order.
- `top_chains` — The top n chains, ranked by the BEST available measurement.
- `layer_split` — Chains grouped by layer. L1 and L2 are NEVER merged.
- `screenable_chains` — Chains the package can actually screen: RPC + DexScreener both work.
- `chain_health` — A matrix of what works where, by capability rather than by chain.
- `discover_memecoins` — Find memecoin candidates on a chain from the chain's top pools.

---

<a id="chains"></a>
## `chains.py`

Multi-chain on-chain data layer: Solana, Ethereum, Base, BSC, Arbitrum.

*784 lines · 6 public functions · 2 classes · layer: Data sources*

**Depends on:** `http`, `models`, `provenance`

**Module constants:**

```python
TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
V2_MINT_TOPIC = '0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f'
V2_BURN_TOPIC = '0x49995e5dd6158cf69ad3e9777c46755a1a826a446c6416992167462dad033b2a'
V3_MINT_TOPIC = '0x9dd857646c181dc756dc3ceba33d06f38e4c3c8bc8fad9990a60679ded73b509'
V3_BURN_TOPIC = '0xd32a1e60019fda299ae8ef8d0ad54483439c1283a4076e3d37ba2a2952d8d12a'
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'
_SSL_CTX = None
```

**Functions**

```python
def dexscreener_pairs(chain: str, token_address: str) -> List[Dict[str, Any]]
def dexscreener_token_profiles(chain: str, token_address: str) -> List[Dict[str, Any]]
def dexscreener_boosted_tokens() -> List[Dict[str, Any]]
def fetch_token_events(chain: str, token_address: Optional[str]=None, limit: int=50) -> Dict[str, Any]
def fetch_wallet_trades(chain: str, wallet: str, limit: int=100, token_address: Optional[str]=None, blocks: int=5000) -> List[WalletTrade]
def chain_health(targets: Optional[List[str]]=None) -> Dict[str, Any]
```

- `dexscreener_pairs` — Real pairs for a token, from DexScreener. Works on all five chains.
- `dexscreener_boosted_tokens` — Tokens DexScreener is currently boosting - a real traction signal.
- `fetch_token_events` — Detect real token / liquidity events on a chain.
- `fetch_wallet_trades` — Real trades for one wallet.
- `chain_health` — Check, live, which chains and data sources are reachable right now.

**Classes**

### `class EVMClient`

Minimal JSON-RPC client for the EVM chains.

```python
def rpc(self, method: str, params: Optional[List[Any]]=None) -> Any
def chain_id(self) -> str
def block_number(self) -> int
def get_block_by_number(self, block: int, full: bool=False) -> Optional[Dict[str, Any]]
def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]
def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]
def get_code(self, address: str, block: Optional[int]=None) -> str
def eth_call(self, to: str, data: str='0x', block: Optional[int]=None) -> str
def get_logs(self, address: Optional[str]=None, topics: Optional[List[Any]]=None, from_block: int=0, to_block: Optional[int]=None, depth: int=0) -> List[Dict[str, Any]]
```

- `get_logs` — eth_getLogs, chunked to stay inside host span limits.

### `class SolanaClient`

Minimal JSON-RPC client for Solana.

```python
def rpc(self, method: str, params: Optional[List[Any]]=None) -> Any
def get_slot(self) -> int
def get_block(self, slot: int, details: bool=False) -> Optional[Dict[str, Any]]
def get_signatures_for_address(self, address: str, limit: int=100, before: Optional[str]=None) -> List[Dict[str, Any]]
def get_transaction(self, signature: str) -> Optional[Dict[str, Any]]
def get_token_accounts(self, owner: str, mint: Optional[str]=None) -> List[Dict[str, Any]]
def get_balance(self, address: str) -> int
def get_account_info(self, address: str) -> Optional[Dict[str, Any]]
def get_latest_blockhash(self) -> Optional[str]
```


---

<a id="crosschain"></a>
## `crosschain.py`

Candidate cross-chain wallet linker.

*1234 lines · 11 public functions · 0 classes · layer: Data sources*

**Depends on:** `costs`, `http`, `provenance`

**Module constants:**

```python
SUGGESTED_THRESHOLD = 0.45
```

**Functions**

```python
def first_funder(address: str, chain: str='ethereum', rpc: Optional[ArchiveRpc]=None, max_backscan_blocks: int=20000) -> Dict[str, Any]
def funder_is_bridge(funder: Optional[str], chain: str='ethereum', rpc: Optional[ArchiveRpc]=None) -> Dict[str, Any]
def wallet_counterparties(address: str, chain: str='ethereum', limit: int=100) -> Dict[str, Any]
def timing_correlation(ts_a: Sequence[Any], ts_b: Sequence[Any], tolerance_seconds: int=3600) -> Dict[str, Any]
def size_similarity(sizes_a: Sequence[float], sizes_b: Sequence[float]) -> Dict[str, Any]
def link_score(a: Dict[str, Any], b: Dict[str, Any], weights: Optional[Dict[str, float]]=None) -> Dict[str, Any]
def find_confirmation(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[Dict[str, Any]]
def find_bridge_flows(address: str, chain: str='ethereum', rpc: Optional[ArchiveRpc]=None, lookback_blocks: int=200000) -> Dict[str, Any]
def build_wallet_profile(address: str, chain: str='ethereum', sizes: Optional[Sequence[float]]=None, timestamps: Optional[Sequence[Any]]=None, rpc: Optional[ArchiveRpc]=None, with_bridge_scan: bool=True) -> Dict[str, Any]
def link_wallets(profiles: Sequence[Dict[str, Any]], weights: Optional[Dict[str, float]]=None) -> Dict[str, Any]
def self_test() -> Dict[str, Any]
```

- `first_funder` — The first address that sent native gas to `address`.
- `funder_is_bridge` — Is the funder a contract, and is it a KNOWN bridge?
- `wallet_counterparties` — The set of addresses this wallet interacts with, plus its
- `timing_correlation` — How tightly do two wallets' activity windows overlap?
- `size_similarity` — Do two wallets trade similar sizes?
- `link_score` — Score ONE pair of wallets.
- `find_confirmation` — Is there an EXPLICIT on-chain artefact linking these wallets?
- `find_bridge_flows` — Look for bridging flows OUT of `address`.
- `build_wallet_profile` — Collect every signal this module can get for ONE wallet on ONE
- `link_wallets` — Score every PAIR of wallet profiles and rank the candidates.
- `self_test` — Offline self-test of the scoring and the confirmation logic.

---

<a id="deployers"></a>
## `deployers.py`

Deployer discovery: derive token deployers from on-chain data.

*398 lines · 5 public functions · 0 classes · layer: Data sources*

**Depends on:** `chains`, `http`, `models`, `provenance`

**Module constants:**

```python
REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state', 'dep
TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'
```

**Functions**

```python
def find_evm_contract_creator(chain: str, address: str, max_calls: int=60) -> Dict[str, Any]
def find_solana_mint_creator(mint: str, use_rugcheck: bool=True) -> Dict[str, Any]
def seed_registry(tokens: List[Dict[str, str]], registry_path: str=REGISTRY_PATH, merge: bool=True) -> Dict[str, Any]
def load_registry(registry_path: str=REGISTRY_PATH) -> Dict[str, Any]
def registry_as_addresses(registry_path: str=REGISTRY_PATH) -> List[str]
```

- `find_evm_contract_creator` — Find the address that deployed an EVM contract.
- `find_solana_mint_creator` — Find the address that created a Solana mint.
- `seed_registry` — Derive deployers for `tokens` and seed the registry from them.
- `registry_as_addresses` — The derived deployer addresses, for the profiler's insider filter.

---

<a id="disclosure"></a>
## `disclosure.py`

US officials' legally-required financial disclosures — all three branches —
plus market-impact analysis.

*1047 lines · 14 public functions · 5 classes · layer: Data sources*

**Depends on:** `http`, `provenance`

**Module constants:**

```python
HOUSE_GLYPH = {'ʇ': 'E', 'ʔ': 'R', 'ʋ': 'I', 'ʑ': 'O', 'ʆ': 'D', 'ʅ': 'C', 'ʃ': 'A',
BRANCHES = {'legislative': {'title': 'Legislative — Members of Congress', 'law': 
HOUSE_FD_INDEX = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}
HOUSE_FD_PDF = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}
HOUSE_PTR_PDF = 'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doci
HOUSE_FILING_TYPES = {'C': 'Candidate Report', 'P': 'Periodic Transaction Report', 'X': 'Fi
OGE_INDEX = 'https://extapps2.oge.gov/201/Presiden.nsf/API.xsp/v3/rest'
OGE_PAGE_SIZE = 100
JEFS_ROOT = 'https://pub.jefs.uscourts.gov/'
FIXTHECOURT_INDEX = 'https://fixthecourt.com/2025disclosures/'
SCOTUSBLOG_INDEX = 'https://www.scotusblog.com/financial-disclosures/'
ASSET_TYPE_CODES = {'ST': 'stock', 'OP': 'option', 'AB': 'partnership/other', 'RP': 'real
# ... and 6 more
```

**Functions**

```python
def decode_house_glyphs(text: str) -> str
def fetch_house_index(year: int=2026) -> Tuple[List[HouseFiling], Provenance]
def extract_pdf_text(pdf_bytes: bytes) -> Optional[str]
def fetch_house_pdf(filing: HouseFiling) -> Tuple[Optional[str], Provenance]
def fetch_oge_index(search: Optional[str]=None, start: int=0, length: int=OGE_PAGE_SIZE) -> Tuple[List[OgeFiling], int, Provenance]
def fetch_oge_all(search: Optional[str]=None, max_pages: int=200) -> Tuple[List[OgeFiling], List[str], Provenance]
def fetch_oge_pdf(filing: OgeFiling) -> Tuple[Optional[str], Provenance]
def fetch_judicial_filings(include_mirrors: bool=True) -> Tuple[List[JudicialFiling], List[Dict[str, Any]]]
def fetch_judicial_text(filing: JudicialFiling) -> Tuple[Optional[str], str]
def classify_oge_document(text: str) -> str
def classify_house_document(text: str) -> str
def extract_assets_from_text(text: str, doc_kind: str='auto') -> List[DisclosedAsset]
def analyse_market_impact(disclosure_date: _dt.date, tickers: Sequence[str], bars_by_symbol: Dict[str, List[Dict[str, Any]]], benchmark: str='SPY', value_by_ticker: Optional[Dict[str, float]]=None) -> Tuple[List[ImpactObservation], List[str]]
def build_disclosure_report(house_year: int=2026, oge_names: Optional[Sequence[str]]=None, include_judicial: bool=True, fetch_pdfs_for: Optional[Sequence[str]]=None) -> Dict[str, Any]
```

- `extract_pdf_text` — Extract a PDF's text layer with PyMuPDF. None when unavailable.
- `fetch_oge_index` — Fetch one page of the OGE PAS index.
- `fetch_oge_all` — Page the whole OGE index for a name. Returns (filings, gaps, provenance).
- `fetch_judicial_filings` — Collect judicial-branch filings.
- `fetch_judicial_text` — Fetch a judicial PDF's text. Returns (text, note).
- `classify_oge_document` — Classify an OGE PDF's text into a document kind.
- `classify_house_document` — Classify a House PDF into house_fd / house_ptr / house_other.
- `extract_assets_from_text` — Pull disclosed assets out of an extracted filing text.
- `analyse_market_impact` — Measure what the market did after a disclosure date.
- `build_disclosure_report` — Assemble the three-branch disclosure report.

**Classes**

### `class HouseFiling`

```python
def is_member(self) -> bool
def is_candidate(self) -> bool
def pdf_url(self) -> str
def to_dict(self) -> Dict[str, Any]
```


### `class OgeFiling`

```python
def to_dict(self) -> Dict[str, Any]
```


### `class JudicialFiling`

```python
def to_dict(self) -> Dict[str, Any]
```


### `class DisclosedAsset`

```python
def to_dict(self) -> Dict[str, Any]
```


### `class ImpactObservation`

```python
def to_dict(self) -> Dict[str, Any]
```


---

<a id="etherscan"></a>
## `etherscan.py`

Etherscan V2 adapter - the one source that needs a key.

*300 lines · 10 public functions · 0 classes · layer: Data sources*

**Depends on:** `http`

**Module constants:**

```python
V2 = 'https://api.etherscan.io/v2/api'
CHAIN_IDS = {'ethereum': 1, 'bnb': 56, 'polygon': 137, 'arbitrum': 42161, 'optimis
_MIN_INTERVAL = 0.25
FREE_TIER_ACTIONS = {'account.tokentx': 'OK - ERC-20 transfers (1,000 per page)', 'account
```

**Functions**

```python
def api_key() -> Optional[str]
def has_key() -> bool
def token_holders(token: str, chain: str='ethereum', limit: int=100, addresses: Optional[List[str]]=None) -> Dict[str, Any]
def token_balances(addresses: List[str], token: str, chain: str='ethereum') -> Dict[str, Any]
def token_balance(address: str, token: str, chain: str='ethereum') -> Dict[str, Any]
def token_holders_from_transfers(token: str, chain: str='ethereum', limit: int=5000) -> Dict[str, Any]
def token_transfers(token: str, chain: str='ethereum', limit: int=1000) -> Dict[str, Any]
def address_transfers(address: str, chain: str='ethereum', limit: int=1000, offset: int=0, token: Optional[str]=None) -> Dict[str, Any]
def balance(address: str, chain: str='ethereum') -> Dict[str, Any]
def contract_source(token: str, chain: str='ethereum') -> Dict[str, Any]
```

- `api_key` — The key, if one is configured. The VALUE is never returned to a
- `token_holders` — Holder balances for an ERC-20.
- `token_balances` — ERC-20 balances for up to 20 addresses, in ONE call.
- `token_balance` — One address's ERC-20 balance.
- `token_holders_from_transfers` — Reconstruct the holders of an ERC-20 from its transfer tape.
- `token_transfers` — Transfers of an ERC-20.
- `address_transfers` — ERC-20 transfers involving one address.
- `balance` — The native balance.
- `contract_source` — The verified source of a contract, if it is verified.

---

<a id="holders"></a>
## `holders.py`

Holder-composition time series, and abrupt ownership change detection.

*555 lines · 12 public functions · 0 classes · layer: Data sources*

**Depends on:** `http`, `memecoin`, `provenance`

**Module constants:**

```python
LIVE = 'LIVE'
SERIES_DIR = os.path.join(os.path.dirname(__file__), 'state', 'holder_series')
SPIKE_PCT_DEFAULT = 50.0
CONCENTRATION_DELTA_PP_DEFAULT = 10.0
MIN_SNAPSHOTS_DEFAULT = 2
KNOWN_NON_HOLDERS_SOLANA = {'5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1', 'GThUX1Atko4tqhN2NaiT
KNOWN_NON_HOLDERS_EVM = {'0x0000000000000000000000000000000000000000', '0x00000000000000000000
TOP_N = 10
_SOL_MIN_INTERVAL = 0.9
```

**Functions**

```python
def top_n_percentage(amounts: List[float], total: float, n: int=TOP_N) -> float
def gini_coefficient(amounts: List[float]) -> float
def hhi(amounts: List[float]) -> float
def nakamoto_coefficient(amounts: List[float]) -> int
def classify_concentration(top10_pct: float, gini: float) -> str
def solana_holder_composition(rpc_url: str, mint: str, top_n: int=TOP_N) -> Dict[str, Any]
def evm_holder_composition(rpc_url: str, token: str, top_n: int=TOP_N, blocks_back: int=4000, log_span_cap: int=5000) -> Dict[str, Any]
def rugcheck_holder_composition(mint: str, top_n: int=TOP_N) -> Dict[str, Any]
def load_series(chain: str, mint: str) -> Dict[str, Any]
def save_series(chain: str, mint: str, series: Dict[str, Any]) -> str
def record_snapshot(chain: str, mint: str, composition: Dict[str, Any], price_usd: Optional[float], price_change_24h: Optional[float], provenance: str=LIVE, source: str='') -> Dict[str, Any]
def detect_ownership_shifts(chain: str, mint: str, spike_pct: float=SPIKE_PCT_DEFAULT, concentration_delta_pp: float=CONCENTRATION_DELTA_PP_DEFAULT, min_snapshots: int=MIN_SNAPSHOTS_DEFAULT) -> Dict[str, Any]
```

- `top_n_percentage` — Percentage of supply held by the top n addresses.
- `gini_coefficient` — Inequality of the holder distribution (0 = equal, 1 = one holder).
- `hhi` — Herfindahl-Hirschman Index of market shares (0-10000).
- `nakamoto_coefficient` — How many holders together control >51% of supply.
- `classify_concentration` — Risk band from the token-holder-analysis skill's thresholds.
- `solana_holder_composition` — Top holders of a Solana mint, resolved to OWNING WALLETS.
- `evm_holder_composition` — Reconstruct ERC-20 holders from Transfer logs.
- `rugcheck_holder_composition` — Holder composition from RugCheck's FULL report (Solana).
- `record_snapshot` — Append one timestamped holder-composition snapshot to the series.
- `detect_ownership_shifts` — Find windows where composition changed abruptly around a price spike.

---

<a id="market"></a>
## `market.py`

Market data: OHLCV, options chains, crypto prices.

*403 lines · 10 public functions · 0 classes · layer: Data sources*

**Depends on:** `http`, `provenance`

**Module constants:**

```python
NASDAQ_OPTION_CHAIN = 'https://api.nasdaq.com/api/quote/{sym}/option-chain?assetclass={ac}&f
NASDAQ_HEADERS = {'Accept': 'application/json, text/plain, */*', 'Referer': 'https://ww
DERIBIT = 'https://www.deribit.com/api/v2/public'
DEXSCREENER_SEARCH = 'https://api.dexscreener.com/latest/dex/search?q={q}'
DEXSCREENER_TOKEN_PAIRS = 'https://api.dexscreener.com/token-pairs/v1/{chain}/{addr}'
```

**Functions**

```python
def fetch_ohlcv(symbol: str, rng: str='10y', interval: str='1d', fetcher: Optional[CachedFetcher]=None, refresh: bool=False, timeout: int=30) -> Tuple[List[Dict[str, Any]], Provenance]
def fetch_many_ohlcv(symbols: Sequence[str], rng: str='10y', interval: str='1d', fetcher: Optional[CachedFetcher]=None, refresh: bool=False) -> Tuple[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]], List[Provenance]]
def closes_and_volumes(bars: Sequence[Dict[str, Any]]) -> Tuple[List[float], List[float]]
def fetch_option_chain(symbol: str, from_date: Optional[str]=None, to_date: Optional[str]=None, fetcher: Optional[CachedFetcher]=None, refresh: bool=False, timeout: int=60) -> Tuple[Dict[str, Any], Provenance]
def fetch_deribit_instruments(currency: str='BTC') -> Tuple[List[Dict[str, Any]], Provenance]
def fetch_deribit_book(currency: str='BTC', kind: str='option') -> Tuple[List[Dict[str, Any]], Provenance]
def fetch_deribit_trades(currency: str='BTC', kind: str='option', limit: int=100) -> Tuple[List[Dict[str, Any]], Provenance]
def fetch_coingecko_prices(coin_ids: Sequence[str], vs: str='usd') -> Tuple[Dict[str, float], Provenance]
def fetch_dex_pairs(query: str, limit: int=30) -> Tuple[List[Dict[str, Any]], Provenance]
def normalise_dex_pair(p: Dict[str, Any]) -> Dict[str, Any]
```

- `fetch_ohlcv` — Fetch OHLCV bars from the Yahoo chart API.
- `fetch_many_ohlcv` — Fetch several symbols. Returns (bars_by_symbol, failures, provenances).
- `fetch_option_chain` — Fetch the full option chain for a US symbol.
- `normalise_dex_pair` — Flatten a DexScreener pair into the fields the meme-coin screen needs.

---

<a id="narrative"></a>
## `narrative.py`

Narrative specificity: is this token a NICHE community, or a generic trend clone?

*555 lines · 7 public functions · 0 classes · layer: Data sources*

**Depends on:** `provenance`

**Module constants:**

```python
COHORT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state', 'nar
NICHE_SCORE_THRESHOLD = 5.0
TREND_KEYWORDS = ('moon', 'pump', 'meme', 'coin', 'token', 'solana', 'sol', 'btc', 'bit
COMMUNITY_PLATFORMS = ('telegram', 'discord', 't.me', 'discord.gg', 'discord.com')
_ALNUM_RE = re.compile('^[A-Za-z0-9]{2,6}$')
_VOWELS = set('aeiouAEIOU')
```

**Functions**

```python
def classify_specificity(profile: Dict[str, Any], pair: Dict[str, Any]) -> Dict[str, Any]
def cohort_baseline(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def relative_to_cohort(row: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]
def backward_association(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def save_cohort(rows: Sequence[Dict[str, Any]], path: str=COHORT_PATH) -> Dict[str, Any]
def select_base_rows(snaps: Sequence[Dict[str, Any]], now: Optional[int]=None, min_gap_seconds: int=3600) -> tuple
def verify_cohort(path: str=COHORT_PATH, min_gap_seconds: int=3600, current_rows: Optional[Sequence[Dict[str, Any]]]=None) -> Dict[str, Any]
```

- `classify_specificity` — Score one token's narrative specificity from free sources.
- `cohort_baseline` — The baseline the clause needs, taken from the cohort itself.
- `relative_to_cohort` — Place one token in its cohort's distribution, BY RANK.
- `backward_association` — BACKWARD association between specificity and 24h performance.
- `save_cohort` — Write a timestamped snapshot so a later run can measure FORWARD returns.
- `select_base_rows` — Select, per token, the EARLIEST qualifying observation.
- `verify_cohort` — Measure FORWARD returns between two snapshots and test the claim.

---

<a id="onchain"></a>
## `onchain.py`

Crypto wallet tracking and transaction analysis.

*571 lines · 10 public functions · 2 classes · layer: Data sources*

**Depends on:** `http`, `provenance`

**Module constants:**

```python
PUBLIC_RPC = 'https://api.mainnet-beta.solana.com'
HELIUS_RPC = 'https://mainnet.helius-rpc.com/?api-key={key}'
HELIUS_API = 'https://api-mainnet.helius-rpc.com/v0'
```

**Functions**

```python
def helius_key() -> Optional[str]
def get_signatures(address: str, limit: int=50, before: Optional[str]=None) -> Tuple[List[Dict[str, Any]], Provenance]
def get_transaction(signature: str) -> Tuple[Dict[str, Any], Provenance]
def get_balance(address: str) -> Tuple[float, Provenance]
def get_token_accounts(address: str) -> Tuple[List[Dict[str, Any]], Provenance]
def get_asset_holders(mint: str) -> Tuple[List[Dict[str, Any]], Provenance]
def parse_transaction(tx: Dict[str, Any]) -> WalletTransaction
def analyse_wallet(address: str, tx_limit: int=50, fetch_transactions: bool=True) -> WalletProfile
def cluster_wallets(wallets: Sequence[WalletProfile], min_shared: int=2) -> Dict[str, Any]
def concentration_report(mint: str) -> Tuple[Dict[str, Any], List[Provenance]]
```

- `get_signatures` — Recent transaction signatures for a wallet.
- `get_transaction` — A single parsed transaction.
- `get_token_accounts` — All token accounts (and their mints) owned by a wallet.
- `get_asset_holders` — Top token accounts for a mint (owner + balance), via getTokenLargestAccounts.
- `analyse_wallet` — Fetch and analyse a wallet's recent activity.
- `cluster_wallets` — Cluster wallets that share funding sources / counterparties.
- `concentration_report` — Top-holder concentration for a token — the paper's structural-risk layer.

**Classes**

### `class WalletTransaction`

```python
def timestamp(self) -> Optional[_dt.datetime]
def counterparties(self) -> List[str]
```


### `class WalletProfile`

```python
def to_dict(self) -> Dict[str, Any]
```


---

<a id="priceatblock"></a>
## `priceatblock.py`

A DIRECT USD price at a PAST BLOCK, computed from the DEX pool itself.

*328 lines · 6 public functions · 0 classes · layer: Data sources*

**Depends on:** `costs`

**Module constants:**

```python
V2_FACTORY = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
WETH = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
USDC = '0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
USDT = '0xdAC17F958D2ee523a2206206994597C13D831ec7'
SEL_GET_PAIR = '0xe6a43905'
SEL_GET_RESERVES = '0x0902f1ac'
SEL_TOKEN0 = '0x0dfe1681'
SEL_TOKEN1 = '0xd21220a7'
SEL_DECIMALS = '0x313ce567'
ZERO = '0x' + '0' * 40
MIN_STABLE_LIQUIDITY = 10000.0
MIN_WETH_LIQUIDITY = 30.0
```

**Functions**

```python
def v2_pair(rpc: ArchiveRpc, token_a: str, token_b: str, block: int) -> Optional[str]
def v2_reserves(rpc: ArchiveRpc, pair: str, block: int) -> Optional[Tuple[int, int]]
def weth_usd(rpc: ArchiveRpc, block: int) -> Optional[Dict[str, Any]]
def usd_price_at_block(token: str, block: int, chain: str='ethereum', rpc: Optional[ArchiveRpc]=None) -> Dict[str, Any]
def price_events_by_block(events: list, chain: str='ethereum', rpc: Optional[ArchiveRpc]=None, min_interval: float=0.12, max_blocks: int=40) -> Dict[str, Any]
def clear_caches() -> None
```

- `v2_pair` — The Uniswap V2 pair that existed for these two tokens at `block`.
- `v2_reserves` — (reserve0, reserve1) of a V2 pair at a block.
- `weth_usd` — The WETH/USD price at a block, from the deep WETH/USDC V2 pair.
- `usd_price_at_block` — The USD price of a token at a past block, from the DEX itself.
- `price_events_by_block` — Price a list of transfer events by their block.

---

<a id="priced"></a>
## `priced.py`

Price a wallet's memecoin trades at HISTORICAL prices and compute a real
cost basis, then run the consistency gate on the result.

*396 lines · 7 public functions · 1 classes · layer: Data sources*

**Depends on:** `costs`, `edge`, `http`, `memecoinscan`, `priceatblock`

**Module constants:**

```python
_MIN_INTERVAL = 1.1
_HOUR = 3600
```

**Functions**

```python
def clear_price_cache() -> None
def price_position_events(position: Dict[str, Any], chain: str='ethereum', throttle: Optional[_Throttle]=None) -> Dict[str, Any]
def price_wallet_positions(profile: Dict[str, Any], chain: str='ethereum', max_events: int=400, throttle: Optional[_Throttle]=None, method: str='auto', max_blocks: int=40) -> Dict[str, Any]
def fifo_closed_trades(trades: List[Dict[str, Any]], price_field: str='price_usd', qty_field: str='qty') -> List[Dict[str, Any]]
def build_gate_trades(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]
def realised_pnl_and_edge(priced: Dict[str, Any], trials_scanned: int=1, basis: str='fifo') -> Dict[str, Any]
def screen_wallet(address: str, universe: Dict[str, Any], chain: str='ethereum', trials_scanned: int=1, max_items: int=400) -> Dict[str, Any]
```

- `clear_price_cache` — Empty the shared price cache.
- `price_position_events` — Price every buy and sell event of one position.
- `price_wallet_positions` — Price every position of one wallet profile.
- `fifo_closed_trades` — Match buys to sells FIFO and produce CLOSED trades.
- `build_gate_trades` — Convert priced transfer events into the trade shape `edge.py` wants.
- `realised_pnl_and_edge` — Compute realised PnL and run the consistency gate on priced trades.
- `screen_wallet` — Full pipeline for one wallet: history -> prices -> PnL -> gate.

**Classes**

### `class _Throttle`

A simple per-host rate limiter.

```python
def wait(self) -> None
```


---

<a id="social"></a>
## `social.py`

Multi-platform social signals and traction measurement.

*866 lines · 6 public functions · 0 classes · layer: Data sources*

**Depends on:** `chains`, `http`, `memecoin`, `provenance`

**Module constants:**

```python
COMMUNITY_PLATFORMS = ('telegram', 'discord', 't.me', 'discord.gg', 'discord.com', 'telegram
BROADCAST_PLATFORMS = ('twitter', 'x.com', 'tiktok', 'instagram', 'youtube', 'facebook', 're
_PLATFORM_ALIASES = {'twitter': 'x', 'x': 'x', 'tiktok': 'tiktok', 'instagram': 'instagram
COMMUNITY_TEXT_MARKERS = ('community', 'cult', 'army', 'lore', 'canon', 'believers', 'holders',
GENERIC_TEXT_MARKERS = ('utility', 'ecosystem', 'defi', 'protocol', 'staking', 'yield', 'apy'
_PROPER_NOUN = re.compile('\\b([A-Z][a-z]{2,}[A-Za-z]*)\\b')
_STOP_CAPS = {'The', 'This', 'That', 'Our', 'Your', 'Their', 'Token', 'Coin', 'Comm
_DEXSCR_GLOBAL_LISTS = (('https://api.dexscreener.com/token-profiles/latest/v1', 'dexscreener
_TG_MEMBER_RE = re.compile('([\\d\\s,\\u00a0\\u202f\\.]+?)\\s*members', re.I)
_TG_ONLINE_RE = re.compile('([\\d\\s,\\u00a0\\u202f\\.]+?)\\s*online', re.I)
_TG_VIEW_RE = re.compile('<title>\\s*Telegram:\\s*View\\s*@', re.I)
```

**Functions**

```python
def analyse_description(text: str) -> Dict[str, Any]
def fetch_telegram_size(url: str) -> Dict[str, Any]
def fetch_discord_size(url: str) -> Dict[str, Any]
def fetch_social_profile(chain: str, token: str, jupiter: bool=False, rugcheck: bool=False) -> Dict[str, Any]
def score_narrative(profile: Dict[str, Any], name_info: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
def score_traction(profile: Dict[str, Any]) -> Dict[str, Any]
```

- `analyse_description` — Classify a project's own description for community vs generic framing.
- `fetch_telegram_size` — Member and online counts from a Telegram channel's public preview.
- `fetch_discord_size` — Member and presence counts from a Discord invite.
- `fetch_social_profile` — Collect every free social + traction signal available for a token.
- `score_narrative` — Turn a social profile into a narrative score + niche verdict.
- `score_traction` — Turn observed market behaviour into a traction score.

---

<a id="source_reliability"></a>
## `source_reliability.py`

Source reliability register: the papers' own defects and this package's scope.

*81 lines · 4 public functions · 0 classes · layer: Data sources*

**Module constants:**

```python
_HERE = os.path.dirname(os.path.abspath(__file__))
REGISTER_PATH = os.path.join(_HERE, 'data', 'source_reliability.json')
```

**Functions**

```python
def load_register(path: str=None) -> Dict[str, Any]
def defect_rows(reg: Dict[str, Any]) -> List[Dict[str, Any]]
def scope_rows(reg: Dict[str, Any]) -> List[Dict[str, Any]]
def register_section(reg: Dict[str, Any]) -> Dict[str, Any]
```

- `load_register` — Load the register. Returns {} when it is absent (degrade, don't crash).
- `defect_rows` — Flatten the register into one row per defect, across all documents.
- `scope_rows` — The paper sections this package deliberately does not implement.
- `register_section` — The report-ready payload for the source-reliability section.

---

<a id="traders"></a>
## `traders.py`

Trader qualification against CITED standards, and a GIPS-consistent
qualified-wallet pool with continuous tracking.

*601 lines · 11 public functions · 0 classes · layer: Data sources*

**Depends on:** `chains`, `provenance`, `stats`

**Module constants:**

```python
POOL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state', 'qua
NIST_SAMPLE_SIZE_URL = 'https://www.itl.nist.gov/div898/handbook/prc/section2/prc242.htm'
NIST_VALIDITY_URL = 'https://www.itl.nist.gov/div898/handbook/prc/section2/prc24.htm'
WILSON_URL = 'https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm'
RULE_OF_THREE_URL = 'https://pubmed.ncbi.nlm.nih.gov/6827763/'
SHARPE_URL = 'https://rpc.cfainstitute.org/sites/default/files/-/media/documents/co
GIPS_URL = 'https://www.gipsstandards.org/wp-content/uploads/2021/03/2020_gips_st
GMGN_URL = 'https://docs.gmgn.ai/index/insider-traders-snipers-first-70-buyers'
NANSEN_FIRST_FUNDER_URL = 'https://docs.nansen.ai/api/profiler/address-first-funder'
NANSEN_COVERAGE_URL = 'https://docs.nansen.ai/api/data-coverage'
```

**Functions**

```python
def required_sample_size(p0: float=0.5, p1: float=0.55, alpha: float=0.05, beta: float=0.2, delta: float=0.05, one_sided: bool=True, continuity_correction: bool=True) -> Dict[str, Any]
def wilson_interval(wins: int, n: int, confidence: float=0.95) -> Dict[str, Any]
def rule_of_three(n: int) -> Dict[str, Any]
def validity_floor(p0: float=0.5) -> Dict[str, Any]
def criteria_table() -> List[Dict[str, Any]]
def qualify_wallet(profile: Dict[str, Any], criteria: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
def load_pool(path: Optional[str]=None) -> Dict[str, Any]
def save_pool(pool: Dict[str, Any], path: Optional[str]=None) -> str
def record_evaluation(address: str, chain: str, verdict: Dict[str, Any], pool: Optional[Dict[str, Any]]=None, path: Optional[str]=None) -> Dict[str, Any]
def pool_report(pool: Optional[Dict[str, Any]]=None, path: Optional[str]=None) -> Dict[str, Any]
def track_wallets(chain: str='solana', limit: int=25, pool: Optional[Dict[str, Any]]=None, path: Optional[str]=None) -> Dict[str, Any]
```

- `required_sample_size` — Minimum N to show p1 is better than p0 (NIST 7.2.4.2).
- `wilson_interval` — Wilson score interval for a win rate (NIST 7.2.4.1).
- `rule_of_three` — 95% upper bound on the rate when zero events were observed.
- `validity_floor` — NIST's validity conditions for the one-proportion test.
- `criteria_table` — Flat, printable view of every criterion with its authority.
- `qualify_wallet` — Judge a wallet profile against the criteria, with the authority of
- `record_evaluation` — Record one evaluation and update the wallet's forward eligibility.
- `pool_report` — The pool, reported with retired wallets' history retained.
- `track_wallets` — Poll the forward cohort for new activity and update their records.

---

<a id="whitelist"></a>
## `whitelist.py`

The whitelist: memecoin whales and consistently successful traders.

*282 lines · 4 public functions · 0 classes · layer: Data sources*

**Depends on:** `provenance`

**Module constants:**

```python
WHITELIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state', 'whi
STATUS_WHITELISTED = 'WHITELISTED'
STATUS_WATCH = 'WATCH'
STATUS_FLUKE = 'FLUKE'
STATUS_RETIRED = 'RETIRED'
```

**Functions**

```python
def load_whitelist(path: Optional[str]=None) -> Dict[str, Any]
def save_whitelist(blob: Dict[str, Any], path: Optional[str]=None) -> str
def record_evaluation(address: str, chain: str, edge: Dict[str, Any], evidence: Optional[Dict[str, Any]]=None, cluster_id: Optional[str]=None, cluster_evidence: Optional[Dict[str, Any]]=None, blob: Optional[Dict[str, Any]]=None, path: Optional[str]=None) -> Dict[str, Any]
def whitelist_report(blob: Optional[Dict[str, Any]]=None, path: Optional[str]=None) -> Dict[str, Any]
```

- `record_evaluation` — Record one edge evaluation and update the whitelist status.
- `whitelist_report` — The whitelist, reported with every rejected candidate visible.

---

# Features & leading indicators

_Indicators, the volatility risk premium, funding/OI_

<a id="cryptoderivs"></a>
## `cryptoderivs.py`

Crypto derivatives: funding, open interest and basis.

*482 lines · 9 public functions · 0 classes · layer: Features & leading indicators*

**Depends on:** `http`, `leading`, `provenance`

**Module constants:**

```python
BYBIT_BASE = 'https://api.bybit.com/v5'
BINANCE_FAPI = 'https://fapi.binance.com'
_FUNDING_INTERVAL_HOURS = 8.0
```

**Functions**

```python
def annualise_funding(rate: float, interval_hours: float=_FUNDING_INTERVAL_HOURS) -> float
def fetch_bybit_funding(symbol: str='BTCUSDT', limit: int=200, days: Optional[int]=None, timeout: int=30) -> Tuple[List[Tuple[int, float]], Provenance]
def fetch_bybit_open_interest(symbol: str='BTCUSDT', interval: str='1d', limit: int=200, days: Optional[int]=None, timeout: int=30) -> Tuple[List[Tuple[int, float]], Provenance]
def fetch_binance_funding(symbol: str='BTCUSDT', limit: int=200, days: Optional[int]=None, timeout: int=30) -> Tuple[List[Tuple[int, float]], Provenance]
def fetch_binance_open_interest(symbol: str='BTCUSDT', period: str='1d', limit: int=200, timeout: int=30) -> Tuple[List[Tuple[int, float]], Provenance]
def funding_zscore(series: Sequence[Tuple[int, float]], window: Optional[int]=None) -> List[Tuple[int, Optional[float]]]
def oi_change(series: Sequence[Tuple[int, float]], window: int=1) -> List[Tuple[int, Optional[float]]]
def fetch_crypto_derivatives(symbol: str='BTCUSDT', venue: str='bybit', limit: int=200, bar_timestamps: Optional[Sequence[int]]=None, interval: str='1d', timeout: int=30) -> Dict[str, Any]
def build_crypto_derivatives_features(funding: Sequence[Tuple[int, float]], open_interest: Optional[Sequence[Tuple[int, float]]]=None, bar_timestamps: Optional[Sequence[int]]=None, interval_hours: float=_FUNDING_INTERVAL_HOURS, max_lag_bars: int=1, oi_window: int=1, source: str='', asset: str='') -> Dict[str, Any]
```

- `annualise_funding` — Scale a periodic funding rate to an annual rate.
- `fetch_bybit_funding` — Historical funding rates from Bybit.
- `fetch_bybit_open_interest` — Historical open interest from Bybit.
- `fetch_binance_funding` — Historical funding rates from Binance.
- `fetch_binance_open_interest` — Historical open interest from Binance.
- `funding_zscore` — The funding rate's z-score over its own history.
- `oi_change` — The CHANGE in open interest over `window` observations, in percent.
- `fetch_crypto_derivatives` — Fetch funding and open interest together and assemble the block.
- `build_crypto_derivatives_features` — Assemble the crypto-derivatives leading features.

> **Gotcha.** Funding and open interest are VENUE-SPECIFIC: Bybit's open interest is not Binance's, and neither is the whole market. Compare within a venue. A funding rate is published at the END of its interval, so the alignment uses the same one-bar publication lag as every other leading series.

---

<a id="gamma"></a>
## `gamma.py`

Dealer gamma exposure and option-flow measures.

*521 lines · 8 public functions · 2 classes · layer: Features & leading indicators*

**Depends on:** `stats`

**Module constants:**

```python
_MONTHS = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7,
CONTRACT_MULTIPLIER = 100
DEFAULT_ASSUMPTIONS = ['Dealer positioning is ASSUMED from customer-side open interest: cust
```

**Functions**

```python
def bs_greeks(spot: float, strike: float, t_years: float, rate: float, iv: float, dividend_yield: float=0.0) -> Dict[str, float]
def bs_price(spot: float, strike: float, t_years: float, rate: float, iv: float, option_type: str, dividend_yield: float=0.0) -> float
def implied_vol_from_price(price: float, spot: float, strike: float, t_years: float, rate: float, option_type: str, dividend_yield: float=0.0, lo: float=0.01, hi: float=5.0) -> Optional[float]
def parse_expiry(text: str, reference: Optional[_dt.date]=None) -> Optional[_dt.date]
def year_fraction(expiry: _dt.date, as_of: Optional[_dt.date]=None) -> float
def compute_gamma_exposure(chain: Dict[str, Any], spot: Optional[float]=None, rate: float=0.04, dividend_yield: float=0.0, as_of_date: Optional[_dt.date]=None, min_oi: float=1.0) -> GammaExposure
def compute_option_flow(chain: Dict[str, Any], spot: Optional[float]=None, rate: float=0.04, dividend_yield: float=0.0, as_of_date: Optional[_dt.date]=None) -> OptionFlow
def merge_flow_and_gamma(flow: OptionFlow, gamma: GammaExposure) -> Dict[str, Any]
```

- `bs_greeks` — Black-Scholes delta, gamma, vega, theta.
- `bs_price` — Black-Scholes European option price.
- `implied_vol_from_price` — Bisection implied vol from a traded premium. None if it does not converge.
- `parse_expiry` — Parse the expiry strings the sources actually use.
- `compute_gamma_exposure` — Compute dealer net gamma exposure from an option chain.
- `compute_option_flow` — Exposure-adjusted option flow.
- `merge_flow_and_gamma` — The paper's combined read: flow says what pressure exists, gamma says

**Classes**

### `class GammaExposure`

```python
def sign(self) -> Optional[int]
def state(self) -> str
def interpretation(self) -> str
def to_dict(self) -> Dict[str, Any]
```

- `state` — The paper's regime read of the gamma sign.
- `interpretation` — The NASDAQ paper's execution mapping, in its own terms.

### `class OptionFlow`

```python
def to_dict(self) -> Dict[str, Any]
```


> **Gotcha.** The dealer side of the gamma exposure is INFERRED from open interest, which does not reveal who holds the option. The magnitude is indicative; the SIGN and the RELATIVE magnitude across expiries carry the information. Open interest is stale.

---

<a id="leading"></a>
## `leading.py`

Leading-indicator features: the forward-looking half of the regime model.

*711 lines · 9 public functions · 0 classes · layer: Features & leading indicators*

**Depends on:** `gamma`, `http`, `market`, `provenance`

**Module constants:**

```python
DERIBIT_DVOL = 'https://www.deribit.com/api/v2/public'
EQUITY_VOL_INDICES = {'^VIX': {'label': 'S&P 500 implied volatility', 'asset': 'us_equity'}
_ANN = math.sqrt(252.0)
_INSTRUMENT_RE = re.compile('^(?P<ccy>[A-Z0-9]+)-(?P<exp>\\d{1,2}[A-Z]{3}\\d{2})-(?P<st
_MONTHS = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7,
```

**Functions**

```python
def implied_vol_series(symbol: str='^VIX', rng: str='2y', interval: str='1d', timeout: int=30) -> Tuple[List[Tuple[int, float]], Provenance]
def dvol_history(currency: str='BTC', days: int=125, resolution: int=3600, max_pages: int=8, timeout: int=45) -> Tuple[List[Tuple[int, float]], Provenance]
def realized_vol_series(closes: Sequence[float], window: int=20) -> List[Optional[float]]
def volatility_risk_premium(iv: Optional[float], rv: Optional[float]) -> Optional[float]
def iv_term_slope(short_iv: Optional[float], long_iv: Optional[float]) -> Optional[float]
def deribit_gamma_exposure(currency: str='BTC', spot: Optional[float]=None, timeout: int=45) -> Tuple[Dict[str, Any], Provenance]
def deribit_option_flow(currency: str='BTC', limit: int=500, timeout: int=45) -> Tuple[Dict[str, Any], Provenance]
def align_to_bars(series: Sequence[Tuple[int, float]], bar_timestamps: Sequence[int], max_lag_bars: int=1) -> List[Optional[float]]
def build_leading_features(iv_series: Sequence[Tuple[int, float]], bar_timestamps: Sequence[int], closes: Optional[Sequence[float]]=None, rv_window: int=20, max_lag_bars: int=1, label: str='', derivatives: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
```

- `implied_vol_series` — Historical implied volatility for an equity index.
- `dvol_history` — Historical implied volatility for a crypto asset, from Deribit.
- `realized_vol_series` — Annualised realised volatility from closes. This is LAGGING.
- `volatility_risk_premium` — Implied minus realised volatility, in percentage points.
- `iv_term_slope` — Short-versus-long implied-volatility spread.
- `deribit_gamma_exposure` — Dealer gamma exposure for a crypto asset, from the live option book.
- `deribit_option_flow` — Net option flow from the live Deribit trade tape.
- `align_to_bars` — Align a timestamped series to a bar grid WITHOUT look-ahead.
- `build_leading_features` — Assemble the leading feature block for a bar grid.

> **Gotcha.** `align_to_bars` is the no-look-ahead rule: a bar at T may only use a measurement published before T. `dvol_history` must be paged at DAILY resolution - the endpoint caps each call at 1,000 points, so hourly resolution covers ~41 days and would leave most of a multi-year panel with no leading input. A missing value is None, never zero.

---

<a id="leadingcache"></a>
## `leadingcache.py`

Cache and panel-resolution helpers for the leading-indicator features.

*255 lines · 6 public functions · 0 classes · layer: Features & leading indicators*

**Depends on:** `leading`, `provenance`

**Module constants:**

```python
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)
MAX_AGE_SECONDS = 24 * 3600
_CRYPTO_CCY = {'BTC': 'BTC', 'BITCOIN': 'BTC', 'ETH': 'ETH', 'ETHEREUM': 'ETH', 'SOL
```

**Functions**

```python
def leading_cache_path(source: str, asset: str) -> str
def store_leading_series(source: str, asset: str, series: Sequence[Tuple[int, float]], url: str='', note: str='') -> str
def load_leading_series(source: str, asset: str, max_age_seconds: Optional[int]=MAX_AGE_SECONDS) -> Tuple[List[Tuple[int, float]], Provenance]
def resolve_leading_source(symbols: Sequence[str]) -> Tuple[str, str, str]
def panel_date_timestamps(dates: Sequence[str]) -> List[int]
def series_for_panel(panel: Any, source: Optional[str]=None, asset: Optional[str]=None, allow_fetch: bool=True) -> Tuple[List[Tuple[int, float]], Dict[str, Any]]
```

- `leading_cache_path` — Where the cached series for (source, asset) lives.
- `store_leading_series` — Write a leading series to the cache and return the path.
- `load_leading_series` — Read a cached leading series.
- `resolve_leading_source` — Decide which leading series applies to a panel's universe.
- `panel_date_timestamps` — Convert the engine's ``YYYY-MM-DD`` date strings to unix seconds.
- `series_for_panel` — Get the leading series for a panel, fetching and caching if needed.

> **Gotcha.** `series_for_panel` resolves the leading source from the universe PRESET, and the cache key must include the source and asset - a cached BTC series served to an equity panel would be a silent corruption.

---

<a id="leadingspecs"></a>
## `leadingspecs.py`

The LEADING-INDICATOR specifications.

*318 lines · 2 public functions · 0 classes · layer: Features & leading indicators*

**Module constants:**

```python
LEADING_SPECS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'lead
_CONFIRMED = ['hypothesis', 'universe', 'direction', 'entry', 'exit', 'timeframe', 
_ANALYST = 'ANALYST_CHOICE: not stated by the paper; chosen to match the '
_ENGINE = "ENGINE_DEFAULT: the engine's default; the paper states no value."
```

**Functions**

```python
def load_leading_specs() -> List[Dict[str, Any]]
def write_leading_specs(path: Optional[str]=None) -> str
```

- `load_leading_specs` — The leading-indicator specs.
- `write_leading_specs` — Write the specs to disk so they are inspectable and reportable.

---

<a id="regime"></a>
## `regime.py`

Market regime identification.

*586 lines · 3 public functions · 2 classes · layer: Features & leading indicators*

**Module constants:**

```python
FEATURE_NAMES = ('vol_level', 'vol_change', 'trend', 'drawdown', 'liquidity')
FEATURE_UNITS = {'vol_level': 'annualised realised volatility of trailing returns', 'v
_LOG_2PI = math.log(2.0 * math.pi)
REGIME_TAXONOMY = ['tranquil_uptrend', 'high_vol_uptrend', 'range_chop', 'regular_bear',
REGIME_BEHAVIOUR = {'tranquil_uptrend': {'momentum': 'on', 'reversal': 'off', 'size': 'fu
```

**Functions**

```python
def build_regime_features(closes: Sequence[float], volumes: Sequence[float], vol_short: int=10, vol_long: int=60, trend_lookback: int=60, drawdown_lookback: int=60, liquidity_lookback: int=20, rebound_lookback: int=20, event_flags: Optional[Sequence[bool]]=None) -> Dict[str, List[Optional[float]]]
def label_states(hmm: HMM, feature_names: Sequence[str]) -> Dict[int, str]
def identify_regimes(features: Dict[str, List[Optional[float]]], feature_names: Sequence[str]=('vol_level', 'vol_change', 'trend', 'drawdown', 'liquidity'), n_states: int=4, max_iter: int=120, standardize: bool=True, min_bars: int=250) -> Optional[RegimeResult]
```

- `build_regime_features` — Build the four core regime features + the rebound/event overlays.
- `label_states` — Assign the paper's labels to latent states using their emission means.
- `identify_regimes` — Fit the HMM and label the states.

**Classes**

### `class HMM`

Gaussian HMM with diagonal covariance.

```python
def fit(self, seq: List[List[float]], max_iter: int=120, tol: float=1e-05) -> 'HMM'
def filter(self, seq: List[List[float]]) -> List[List[float]]
def smooth(self, seq: List[List[float]]) -> List[List[float]]
def viterbi(self, seq: List[List[float]]) -> List[int]
def to_dict(self) -> Dict[str, Any]
```

- `filter` — CAUSAL posterior P(S_t | x_1..t). Safe for backtesting.
- `smooth` — Posterior P(S_t | x_1..T). RETROSPECTIVE ONLY — look-ahead if used live.
- `viterbi` — Most likely state path (uses the whole series).

### `class RegimeResult`

```python
def probability_of(self, label: str, series: str='filtered') -> List[Optional[float]]
def summary(self) -> Dict[str, Any]
```


> **Gotcha.** The HMM is a FILTER, not a smoother - smoothing uses the future and would be look-ahead. The parameters are fitted on the whole panel, so the regime CLASSIFICATION is in-sample; that is disclosed in every report that uses it.

---

# Signals

_Features -> positions: regime switch, ensembles, pairs_

<a id="ensemble"></a>
## `ensemble.py`

The long/short hedged ensemble: the answer to "higher upside than
downside, with consistency".

*415 lines · 2 public functions · 0 classes · layer: Signals*

**Depends on:** `paperspecs`

**Functions**

```python
def signal_ensemble_blend(panel, features: Dict[str, Any], members: Optional[Sequence[Dict[str, Any]]]=None, min_agreement: int=2, rank_floor: float=0.3, invert_signal: bool=False, **kw) -> Dict[str, List[float]]
def ensemble_spec(asset_class: str, params: Optional[Dict[str, Any]]=None, name: Optional[str]=None) -> Dict[str, Any]
```

- `signal_ensemble_blend` — Blend the concept features into one long/short signal.
- `ensemble_spec` — Build the ensemble spec for one asset class.

> **Gotcha.** `rank_floor` is a FLOOR: raising it makes the book MORE selective. It is applied to the MEAN rank of the members that AGREE, not to the most extreme rank across all members - a name that is top-ranked on a member voting the other way is not evidence for the position.

---

<a id="stats"></a>
## `stats.py`

Shared statistical primitives.

*194 lines · 7 public functions · 0 classes · layer: Signals*

**Module constants:**

```python
EULER_GAMMA = 0.5772156649015329
```

**Functions**

```python
def norm_cdf(x: float) -> float
def poly(coeffs: Tuple[float, ...], x: float) -> float
def norm_ppf(p: float) -> float
def binomial_tail_p(wins: int, n: int) -> float
def expected_max_sharpe(n_trials: int) -> float
def deflated_sharpe_ratio(sharpe: float, n_obs: int, n_trials: int, skew: float=0.0, kurtosis: float=3.0) -> Tuple[Optional[float], Dict[str, Any]]
def bayesian_skill_probability(wins: int, n: int) -> Optional[float]
```

- `poly` — Horner evaluation of a coefficient list.
- `norm_ppf` — Inverse normal CDF (Acklam), used for the DSR threshold.
- `binomial_tail_p` — P(X <= wins) for X ~ Binomial(n, 0.5), EXACTLY (integer arithmetic).
- `expected_max_sharpe` — E[max SR] over N independent trials under the null of zero skill.
- `deflated_sharpe_ratio` — The Deflated Sharpe Ratio, and the detail behind it.
- `bayesian_skill_probability` — P(the true win rate > 0.5) with a uniform Beta(1,1) prior.

---

<a id="trend"></a>
## `trend.py`

The paper's LONG/SHORT trend rule, and the pairs-trading spread.

*344 lines · 4 public functions · 0 classes · layer: Signals*

**Depends on:** `backtest`

**Functions**

```python
def sig_trend_long_short(panel, features, feature=None, threshold=0.0, dead_band=0.0, invert_signal=False, **kw) -> Dict[str, List[float]]
def select_pairs(panel, lookback: int=252, max_pairs: int=5) -> List[Tuple[str, str]]
def bt_closes(panel, sym) -> List[Optional[float]]
def sig_pairs_mean_reversion(panel, features, pairs=None, betas=None, lookback_stats: int=60, z_entry: float=2.0, z_exit: float=0.5, max_hold_bars: int=20, max_pairs: int=3, pair_lookback: int=252, invert_signal: bool=False, **kw) -> Dict[str, List[float]]
```

- `sig_trend_long_short` — The paper's trend rule, with BOTH legs live.
- `select_pairs` — The pairs most likely to mean-revert.
- `bt_closes` — The close series for one symbol, without importing the engine.
- `sig_pairs_mean_reversion` — Dollar-neutral pairs mean-reversion, across SEVERAL pairs.

> **Gotcha.** `sig_trend_long_short` is the paper's rule with BOTH legs live; the engine's own `time_series_threshold` only goes long OR short, never both. The pairs signal selects its pairs from the panel by spread stability, and the z-score is measured over a TRAILING window - a whole-sample z-score would be look-ahead.

---

# Portfolio & risk

_Sizing, covariance, risk parity, caps, kill switch_

<a id="costs"></a>
## `costs.py`

Per-wallet realised PnL for free, with NO historical price API.

*1416 lines · 14 public functions · 1 classes · layer: Portfolio & risk*

**Depends on:** `http`, `provenance`

**Module constants:**

```python
ARCHIVE_SUPPORTED = tuple(ARCHIVE_RPC.keys())
SEL_GET_RESERVES = '0x0902f1ac'
SEL_SLOT0 = '0x3850c7bd'
SEL_TOKEN0 = '0x0dfe1681'
SEL_TOKEN1 = '0xd21220a7'
SEL_DECIMALS = '0x313ce567'
SEL_TOTAL_SUPPLY = '0x18160ddd'
TOPIC_V2_SWAP = '0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822'
TOPIC_V3_SWAP = '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'
WETH = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
USDC = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
USD_TOKENS = {USDC}
# ... and 7 more
```

**Functions**

```python
def defillama_price(chain: str, token: str, timestamp: int) -> Dict[str, Any]
def defillama_current_price(chain: str, token: str) -> Dict[str, Any]
def geckoterminal_ohlcv(chain: str, pool: str, timeframe: str='hour', limit: int=1000, before_timestamp: Optional[int]=None) -> Dict[str, Any]
def read_pool_state(pool: str, block: int, chain: str='ethereum', rpc: Optional[ArchiveRpc]=None) -> Dict[str, Any]
def pool_price_for_token(state: Dict[str, Any], token: str) -> Dict[str, Any]
def swap_price_from_logs(pool: str, block: int, token: str, chain: str='ethereum', rpc: Optional[ArchiveRpc]=None) -> Dict[str, Any]
def price_trade(trade: Dict[str, Any], chain: str='ethereum', method: str='auto', rpc: Optional[ArchiveRpc]=None) -> Dict[str, Any]
def fifo_cost_basis(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def weighted_average_cost_basis(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def quantity_proxy(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def proxy_bias_test() -> Dict[str, Any]
def wallet_realised_pnl(trades: Sequence[Dict[str, Any]], chain: str='ethereum', method: str='auto', basis: str='fifo', price_first: bool=True) -> Dict[str, Any]
def prices_or_raw(priced: List[Dict[str, Any]], trades: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]
def self_test() -> Dict[str, Any]
```

- `defillama_price` — Historical price for a token at a unix timestamp. Keyless.
- `geckoterminal_ohlcv` — OHLCV candles for a POOL. Keyless, but the public tier refuses
- `read_pool_state` — Read a Uniswap V2 pair or V3 pool's own state at a PAST block.
- `pool_price_for_token` — Express `state`'s price for `token` in terms of the other leg.
- `swap_price_from_logs` — Read the pool's own Swap event(s) in one block.
- `price_trade` — Price ONE trade, degrading honestly.
- `fifo_cost_basis` — FIFO cost basis over priced trades.
- `weighted_average_cost_basis` — Weighted-average cost basis over priced trades.
- `quantity_proxy` — A PnL PROXY that needs no price at all.
- `proxy_bias_test` — MEASURE the quantity proxy's bias on a case where the truth is
- `wallet_realised_pnl` — Realised PnL for one wallet from its transfer history.
- `prices_or_raw` — Give the quantity proxy every trade (priced or not).
- `self_test` — Offline self-test: the cost-basis engines and the proxy.

**Classes**

### `class ArchiveRpc`

Keyless archive-capable JSON-RPC client.

```python
def remember_archive(self, url: str) -> None
def verify_archive(self, probe_block: Optional[int]=None) -> Dict[str, Any]
def call(self, to: str, data: str, block: Any) -> Dict[str, Any]
def get_block(self, block: Any, full: bool=False) -> Dict[str, Any]
def get_logs(self, address: str, topics: List[str], from_block: int, to_block: int) -> Dict[str, Any]
```

- `remember_archive` — Record a provider that served historical state.
- `verify_archive` — Prove a provider can serve HISTORICAL STATE, not just headers.
- `call` — eth_call. Returns {ok, result, http_status, url, rpc_error}.

> **Gotcha.** The cost model the friction module and the price-at-block tools share.

---

<a id="friction"></a>
## `friction.py`

Friction-aware meme-coin backtesting: slippage, latency, fees, failed
transactions, rug injection, MEV sandwiches and a finite-bankroll
copy-trading simulator.

*1401 lines · 2 public functions · 14 classes · layer: Portfolio & risk*

**Depends on:** `models`, `provenance`

**Module constants:**

```python
MIN_TRADE_USD = 1.0
```

**Functions**

```python
def price_at_or_before(series: Sequence[Tuple[int, float]], ts: int) -> Optional[Tuple[int, float]]
def run_simulation(signals: Sequence[WalletTrade], price_series: Sequence[Tuple[int, float]], friction: Optional[Friction]=None, bankroll: Optional[float]=None, rug_config: Optional[RugConfig]=None, mev_config: Optional[MEVConfig]=None, seed: int=0, config: Optional[CopyConfig]=None, candidates: Optional[Dict[str, TokenCandidate]]=None, price_provenance: str=SYNTHETIC, signal_provenance: Optional[str]=None, source: str='', notes: str='') -> SimulationResult
```

- `price_at_or_before` — The most recent price observable at `ts` (never a future price).
- `run_simulation` — Run one friction-aware copy-trading simulation.

**Classes**

### `class PriceSeries`

A sorted (ts, px) series with O(log n) causal price lookup.

```python
def at_or_before(self, ts: int) -> Optional[Tuple[int, float]]
def last(self) -> Optional[Tuple[int, float]]
```


### `class Fill`

The outcome of one simulated order.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class FrictionModel`

Execution friction, wrapping the shared `models.Friction` contract.

```python
def slippage_bps(self) -> float
def mev_penalty_bps(self) -> float
def failed_tx_rate(self) -> float
def latency_seconds(self) -> float
def priority_fee_usd(self) -> float
def gas_usd(self) -> float
def apply_slippage(self, px: float, side: str) -> float
def apply_mev(self, px: float, side: str, rng: random.Random, qty: Optional[float]=None) -> Tuple[float, float]
def total_cost_usd(self, notional: float, priority_fee: Optional[float]=None, gas: Optional[float]=None) -> float
def simulate_fill(self, px: float, side: str, notional: float, rng: random.Random) -> Fill
def latency_shift(self, ts: int, latency_seconds: Optional[float]=None) -> int
```

- `apply_slippage` — Adverse slippage: buys pay up, sells receive less.
- `apply_mev` — Sandwich penalty from a front-running bot.
- `total_cost_usd` — Modelled friction cost of a trade of `notional` USD.
- `simulate_fill` — Simulate one order end to end.
- `latency_shift` — Execution timestamp: the decision time moved LATER.

### `class RugConfig`

How rugs are injected into a historical price series.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class RugEvent`

One injected rug / liquidity removal, recorded for audit.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class RugInjector`

Inject random rug pulls (80-99% drops) into a price series.

```python
def inject(self, points: Sequence[Tuple[int, float]], token: str='') -> Tuple[List[Tuple[int, float]], List[RugEvent]]
```

- `inject` — Return (rugged series, events). The input is not modified.

### `class MEVConfig`

Sandwich attack parameters.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class MEVOrder`

One intended order (what we wanted to trade).

```python
def to_flat(self) -> Dict[str, Any]
```


### `class MEVEvent`

The penalty applied to one order.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class MEVSimulator`

Apply a randomised sandwich penalty to a series of intended orders.

```python
def apply_to_orders(self, orders: Sequence[Any]) -> List[MEVEvent]
```

- `apply_to_orders` — Penalise every intended order; returns one event per order.

### `class CopyConfig`

Copy-trading rules and sizing.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class TradeRecord`

A `CopyTrade` plus the simulation detail the ledger needs.

```python
def to_flat(self) -> Dict[str, Any]
```


### `class SimulationResult`

Everything a simulation produced, in flattener-friendly form.

```python
def to_flat(self) -> Dict[str, Any]
def to_json(self) -> str
```

- `to_flat` — Shallow, flattener-friendly dict (the package convention).

### `class CopyTradeSimulator`

Follow a set of wallets with a FINITE bankroll.

```python
def run(self, signals: Sequence[WalletTrade], price_series: Any, seed: Optional[int]=None) -> SimulationResult
```


> **Gotcha.** The cost model. Costs are stressed to 2x the engine default in the paper matrix, which is what separates 'real but untradeable at this size' from 'no edge at all'.

---

<a id="portfolio"></a>
## `portfolio.py`

Risk-managed portfolio construction.

*612 lines · 7 public functions · 0 classes · layer: Portfolio & risk*

**Functions**

```python
def estimate_covariance(returns: Sequence[Sequence[Optional[float]]], shrinkage: float=0.3) -> Tuple[List[List[float]], List[str]]
def ewma_volatility(returns: Sequence[Optional[float]], lam: float=0.94) -> float
def blended_volatility(returns: Sequence[Optional[float]], realised_window: int=60, ewma_lambda: float=0.94, ewma_weight: float=0.5) -> float
def risk_parity_weights(cov: Sequence[Sequence[float]], names: Optional[Sequence[str]]=None, tol: float=1e-08, max_iter: int=500) -> Dict[str, Any]
def drawdown_scaler(drawdown_pct: float, soft_limit: float=0.05, hard_limit: float=0.2, floor: float=0.0) -> float
def build_risk_managed_weights(signals: Dict[str, Sequence[Optional[float]]], returns: Optional[Dict[str, Sequence[Optional[float]]]]=None, asset_class: Optional[Dict[str, str]]=None, target_vol: float=0.15, vol_lookback: int=60, ewma_lambda: float=0.94, ewma_weight: float=0.5, shrinkage: float=0.3, gross_leverage: float=1.0, max_position: float=0.1, net_target: Optional[float]=0.0, drawdown_pct: float=0.0, dd_soft_limit: float=0.05, dd_hard_limit: float=0.2, dd_floor: float=0.0, class_caps: Optional[Dict[str, float]]=None) -> Dict[str, Any]
def portfolio_risk_report(weights: Dict[str, float], returns: Optional[Dict[str, Sequence[Optional[float]]]]=None, cov: Optional[Sequence[Sequence[float]]]=None, asset_class: Optional[Dict[str, str]]=None, target_vol: float=0.15) -> Dict[str, Any]
```

- `estimate_covariance` — Sample covariance with shrinkage toward a scaled diagonal.
- `ewma_volatility` — Exponentially weighted volatility (RiskMetrics' lambda).
- `blended_volatility` — A blend of the long realised volatility and the faster EWMA.
- `risk_parity_weights` — Equal-risk-contribution weights for a covariance matrix.
- `drawdown_scaler` — Scale exposure down as the account's drawdown deepens.
- `build_risk_managed_weights` — Build risk-managed target weights from raw signals.
- `portfolio_risk_report` — Report the SHAPE of a book's risk, not just its size.

> **Gotcha.** The risk-parity update must work on risk SHARES, which are scale-invariant, not absolute contributions, which are not - the absolute form fights the renormalisation and never converges. The risk contributions are divided by Sigma SQUARED so they sum to 1 and read as a share of risk. The caps are applied LAST; anything upstream that scales the book must not be able to undo them.

---

<a id="riskguard"></a>
## `riskguard.py`

Code-enforced kill switch + anomaly log (operator brief, quadrants 3 and 4).

*798 lines · 3 public functions · 3 classes · layer: Portfolio & risk*

**Depends on:** `models`, `provenance`

**Module constants:**

```python
DEFAULT_MAX_DRAWDOWN_PCT = 0.2
DEFAULT_DRAWDOWN_WINDOW_SECONDS = 900
DEFAULT_MIN_LIQUIDITY_USD = 1000.0
DEFAULT_MAX_SLIPPAGE_BPS = 500.0
STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state')
DEFAULT_STATE_PATH = os.path.join(STATE_DIR, 'kill_switch.json')
DEFAULT_ANOMALY_PATH = os.path.join(STATE_DIR, 'anomaly_log.json')
SEVERITIES = ('low', 'medium', 'high', 'critical')
_CLEAR_SENTINEL = object()
```

**Functions**

```python
def state_json(ks: KillSwitch) -> str
def rug_signal_details(token_state: Any) -> List[Dict[str, Any]]
def detect_rug_signals(token_state: Any) -> List[str]
```

- `state_json` — Flat JSON of the switch state, for the flattener.
- `rug_signal_details` — Structured rug signals for one token's live state.
- `detect_rug_signals` — Risk flags for one token's live state, shaped to drop straight into

**Classes**

### `class _GuardedKillState(KillSwitchState)`

`KillSwitchState` whose `halted` flag can only be CLEARED by reset().

### `class KillSwitch`

CODE-ENFORCED trading halt. The LLM cannot override this.

```python
def check(self, equity_usd: Optional[float], ts: int, liquidity_usd: Optional[float]=None, token: Optional[str]=None, slippage_bps: Optional[float]=None) -> Tuple[bool, str]
def halt(self, reason: str, trigger: str, ts: Optional[int]=None) -> KillSwitchState
def reset(self, by: str, reason: str, ts: Optional[int]=None, equity_usd: Optional[float]=None) -> KillSwitchState
def to_flat(self) -> Dict[str, Any]
def save(self, path: Optional[str]=None) -> str
def load(self, path: Optional[str]=None) -> bool
def verify_no_bypass(self) -> Dict[str, Any]
```

- `check` — May we trade right now? Returns `(allowed, reason)`. `reason` is
- `halt` — Halt trading. Idempotent; the FIRST reason is the one kept.
- `reset` — Clear the halt. REQUIRES an actor and a non-empty reason.
- `save` — Persist the halt so a restarted process does NOT resume trading.
- `load` — Reload a persisted halt. True when a state file was read.
- `verify_no_bypass` — Prove the 'cannot be overridden' claim against this module's source.

### `class AnomalyLog`

Record unprecedented market conditions and promote them to Known Unknowns.

```python
def load(self, path: Optional[str]=None) -> bool
def save(self, path: Optional[str]=None) -> str
def record(self, kind: str, description: str, market_state: Dict[str, Any], severity: str='medium', action_taken: str='', chain: str='', token: str='', symbol: str='', ts: Optional[int]=None) -> Anomaly
def promote_to_known_unknown(self, anomaly: Anomaly, lesson: str) -> Dict[str, Any]
def replay_known_unknowns(self, price_series: Any) -> List[Dict[str, Any]]
def to_flat(self) -> Dict[str, Any]
```

- `record` — Log one anomaly with the exact market conditions that produced it.
- `promote_to_known_unknown` — Convert an Unknown Unknowing into a replayable Known Unknown.
- `replay_known_unknowns` — Scan a price series for the recorded conditions.

> **Gotcha.** `KillSwitch` persists a halt state. A halt is authoritative: it blocks ENTER and the reason is surfaced, not swallowed.

---

# Backtest engine

_The strategy-backtest-lab gauntlet, walk-forward, costs_

<a id="backtest"></a>
## `backtest.py`

Strategy backtesting.

*2291 lines · 6 public functions · 1 classes · layer: Backtest engine*

**Depends on:** `ensemble`, `leading`, `leadingcache`, `provenance`, `regime`, `specs_2_0`, `trend`

**Module constants:**

```python
SKILL_SCRIPTS = os.path.join(os.environ.get('HERMES_HOME', os.path.join(os.path.expand
ENGINE_AVAILABLE = os.path.isdir(SKILL_SCRIPTS)
ENGINE_IMPORT_ERROR = '' if ENGINE_AVAILABLE else f'strategy-backtest-lab scripts not found 
```

**Functions**

```python
def register_extensions(btengine: Any) -> Dict[str, Any]
def all_specs() -> List[Dict[str, Any]]
def apply_intake_gate(spec: Dict[str, Any]) -> Dict[str, Any]
def run_spec(spec: Dict[str, Any], quick: bool=False, n_variants: Optional[int]=None, walk_forward_folds: int=5, alt_universes: Optional[List[Dict[str, Any]]]=None, out_dir: Optional[str]=None, verbose: bool=True) -> BacktestResult
def run_all_specs(specs: Optional[Sequence[Dict[str, Any]]]=None, quick: bool=False, out_dir: Optional[str]=None, verbose: bool=True) -> List[BacktestResult]
def spec_catalog() -> List[Dict[str, Any]]
```

- `register_extensions` — Register the paper-derived features and signals with the engine.
- `all_specs` — Every paper-derived spec: the hand-built ones plus the LeapSpace 2.0 set.
- `apply_intake_gate` — Run the backtest lab's INTAKE GATE against a spec.
- `run_spec` — Run one spec through the full validation gauntlet.
- `spec_catalog` — A compact catalogue of the paper-derived specs, with provenance.

**Classes**

### `class BacktestResult`

```python
def to_dict(self) -> Dict[str, Any]
```


> **Gotcha.** The engine's `base` block is the IN-SAMPLE run and its `sharpe` is the in-sample Sharpe; the pooled OUT-OF-SAMPLE Sharpe lives on the walk-forward block as `oos_sharpe`. Never let one fall through to the other. A crash is an ERROR, not an INCONCLUSIVE. Every signal must read `invert_signal` or its negative control is a no-op that cannot fail. `register_extensions` injects into the SHARED skill's registries, so a signal type rename can change the engine's behaviour silently (the exact-string test in the conviction-ranking branch).

---

<a id="paperrun"></a>
## `paperrun.py`

The paper-concept runner.

*409 lines · 3 public functions · 0 classes · layer: Backtest engine*

**Depends on:** `backtest`, `leading`, `leadingcache`

**Module constants:**

```python
PAPER_RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)
_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)
```

**Functions**

```python
def merge_results(path: str, rows: Sequence[Dict[str, Any]]) -> str
def leading_coverage_for(spec: Dict[str, Any]) -> Dict[str, Any]
def run_matrix(specs: Sequence[Dict[str, Any]], quick: bool=False, out_path: Optional[str]=None, log_path: Optional[str]=None, only: Optional[Sequence[str]]=None, n_variants: Optional[int]=None) -> Dict[str, Any]
```

- `merge_results` — Merge rows into the results file BY NAME, keeping the file order.
- `leading_coverage_for` — How much leading-indicator data actually covers this spec's panel.
- `run_matrix` — Run the specs and merge the results.

> **Gotcha.** `merge_results` merges BY NAME under an exclusive lock. A read-modify-write without the lock is a lost-update race, and with parallel workers that silently drops rows. The row's `oos_sharpe` comes from the walk-forward block - never from `base['sharpe']`, which is the in-sample number.

---

<a id="paperspecs"></a>
## `paperspecs.py`

The PAPER-CONCEPT specification set.

*808 lines · 4 public functions · 0 classes · layer: Backtest engine*

**Depends on:** `ensemble`

**Module constants:**

```python
PAPER_SPECS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'pape
_PAPER = 'paper'
_ANALYST = 'analyst_choice'
_ENGINE = 'engine_default'
_BUILDERS = {'C1': _c1_regime_switch, 'C2': _c2_leading_vrp, 'C3': _c3_vol_regime_
```

**Functions**

```python
def build_specs(concepts: Optional[List[str]]=None, asset_classes: Optional[List[str]]=None) -> List[Dict[str, Any]]
def build_negative_controls(specs: Optional[List[Dict[str, Any]]]=None) -> List[Dict[str, Any]]
def load_paper_specs(include_controls: bool=True) -> List[Dict[str, Any]]
def write_paper_specs(path: Optional[str]=None) -> str
```

- `build_specs` — Build the paper-concept spec matrix.
- `build_negative_controls` — Build inverted-polarity twins of the real specs.
- `load_paper_specs` — The specs, read from disk when the file exists, else built.
- `write_paper_specs` — Write the full matrix (specs + controls) to disk.

> **Gotcha.** Every spec carries the CONSTANT risk block so a difference in the result is attributable to the market and not to the bookkeeping. `_make` sets that block; a spec must NOT pass its own `portfolio` argument.

---

<a id="quant"></a>
## `quant.py`

On-chain memecoin quant CLI: chains, profiling, consensus, simulation, risk.

*1370 lines · 17 public functions · 0 classes · layer: Backtest engine*

**Depends on:** `backtest`, `biasaudit`, `chainregistry`, `chains`, `cmd_extra`, `crosschain`, `deployers`, `friction`, `holders`, `market`, `memecoin`, `memecoinscan`, `models`, `narrative`, `priced`, `profiler`, `provenance`, `riskguard`, `social`, `socialedge`, `viz`

**Module constants:**

```python
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'oper
STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state')
CONFIG_KEY_ALIASES = {'copy_trade': {'position_pct': 'size_pct', 'max_concurrent_positions'
OPERATOR_OPENING = 'Which blockchains are we targeting today, and do you have a specific 
```

**Functions**

```python
def load_config(path: str=CONFIG_PATH) -> Dict[str, Any]
def cmd_chains(args) -> int
def cmd_profile(args) -> int
def cmd_consensus(args) -> int
def cmd_pool(args) -> int
def cmd_simulate(args) -> int
def cmd_risk(args) -> int
def cmd_anomaly(args) -> int
def cmd_audit(args) -> int
def cmd_viz(args) -> int
def cmd_narrative(args) -> int
def cmd_landscape(args) -> int
def cmd_social(args) -> int
def cmd_socialedge(args) -> int
def cmd_pnl(args) -> int
def cmd_link(args) -> int
def add_parsers(sub) -> None
```

- `cmd_chains` — Which chains are we targeting today, and are they actually reachable?
- `cmd_profile` — Profile one wallet against the operator's consistency thresholds.
- `cmd_consensus` — Did >=N profiled wallets act on the same token inside the window?
- `cmd_pool` — Inspect, add to, or re-evaluate the trusted wallet pool.
- `cmd_simulate` — Run a friction-aware copy-trading simulation over a price series.
- `cmd_risk` — Inspect or reset the code-enforced kill switch.
- `cmd_anomaly` — Show the anomaly log and the promoted Known Unknowns.
- `cmd_audit` — Audit the specs and the stored backtest results for hidden bias.
- `cmd_viz` — Build the visual report: PNG charts + an HTML dashboard.
- `cmd_narrative` — Narrative specificity: classify a token, or run the forward test.
- `cmd_landscape` — The memecoin chain registry: ranked, layered, and honest about gaps.
- `cmd_social` — Narrative specificity and traction for one token on one chain.
- `cmd_socialedge` — The social-edge test: did a wallet buy BEFORE the traction spike?
- `cmd_pnl` — A wallet's real cost basis, priced at each trade's own block.
- `cmd_link` — Cross-chain identity: score every pair of wallets, with evidence.
- `add_parsers` — Register the quant subcommands on an existing subparser action.

> **Gotcha.** The friction-aware simulator. `TradeRecord` and `RugEvent` are DATACLASSES, so field access is `getattr`, not `.get()`; the skipped-trade reason lives on the nested `trade` object, not on the outer record. Statistics are written to `stderr` so `--json` stdout stays parseable.

---

<a id="specs_2_0"></a>
## `specs_2_0.py`

Loads the LeapSpace 2.0 strategy specs.

*62 lines · 2 public functions · 0 classes · layer: Backtest engine*

**Module constants:**

```python
SPEC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'leap
```

**Functions**

```python
def load_specs() -> List[Dict[str, Any]]
def spec_summary() -> List[Dict[str, Any]]
```

- `load_specs` — Load the LeapSpace 2.0 specs from disk.

---

# Validation

_PBO, CPCV, edge scoring, negative controls_

<a id="biasaudit"></a>
## `biasaudit.py`

Bias auditor — look-ahead, survivorship and overfitting (operator brief,
quadrant 3: UNKNOWN KNOWLEDGE).

*832 lines · 4 public functions · 0 classes · layer: Validation*

**Depends on:** `backtest`, `models`

**Module constants:**

```python
FORWARD_PARAM_NAMES = ('shift', 'forward', 'future', 'lead', 'ahead', 'next_bar', 'next_day'
KNOWN_LEAKY_NAMES = ('future_return', 'forward_return', 'next_return', 'future_price', 'fo
RE_EVM_ADDRESS = re.compile('\\b0x[a-fA-F0-9]{40}\\b')
RE_BASE58_MINT = re.compile('\\b[1-9A-HJ-NP-Za-km-z]{32,44}\\b')
CONVENTIONAL_LOOKBACKS = {5, 10, 14, 20, 21, 30, 40, 50, 60, 63, 90, 100, 120, 126, 180, 200, 2
```

**Functions**

```python
def specificity_score(spec: Dict[str, Any]) -> Dict[str, Any]
def audit_spec(spec: Dict[str, Any], price_series: Optional[Any]=None, universe: Optional[Sequence[str]]=None) -> List[BiasFinding]
def audit_report(findings: Sequence[BiasFinding]) -> str
def audit_backtest_results(results: Any, specs: Optional[Sequence[Dict[str, Any]]]=None) -> List[BiasFinding]
```

- `specificity_score` — How specific-to-sample this spec's rules are. Higher = more suspicious.
- `audit_spec` — Audit one strategy spec for look-ahead, survivorship and overfitting.
- `audit_report` — A flat, readable summary of the findings.
- `audit_backtest_results` — Audit the STORED backtest results for hidden bias.

---

<a id="criteria"></a>
## `criteria.py`

Load the agent-researched, authority-tagged consistency criteria and
expose them to the gate.

*139 lines · 10 public functions · 0 classes · layer: Validation*

**Module constants:**

```python
CRITERIA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'consistency_criteria.
```

**Functions**

```python
def load_criteria(path: Optional[str]=None) -> Dict[str, Any]
def criteria_index(spec: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
def criterion(key: str, spec: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
def cited_thresholds(spec: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
def analyst_thresholds(spec: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
def fluke_test_specs(spec: Optional[Dict[str, Any]]=None) -> List[Dict[str, Any]]
def verdict_semantics(spec: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
def tag_definitions(spec: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
def criteria_table(spec: Optional[Dict[str, Any]]=None) -> List[Dict[str, Any]]
def derived_scoring(spec: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
```

- `load_criteria` — The full criteria spec.
- `criteria_index` — criteria keyed by key, for O(1) lookup.
- `criterion` — One criterion, with its authority, tag and URL.
- `cited_thresholds` — Thresholds that carry a real citation.
- `analyst_thresholds` — Thresholds that are the analyst's own, with no published source.
- `fluke_test_specs` — The fluke tests from the spec, with their definitions.
- `verdict_semantics` — How each verdict is defined in the spec.
- `criteria_table` — A flat, printable index: key, threshold, tag, authority, url.

---

<a id="edge"></a>
## `edge.py`

Edge and consistency: separating a consistently profitable trader from a
one-shot winner.

*948 lines · 9 public functions · 0 classes · layer: Validation*

**Depends on:** `gate_tests`, `pbo`, `stats`, `traders`

**Functions**

```python
def independent_bets(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def time_disjoint_bets(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def bet_outcomes(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def drawdown_duration(returns: Sequence[float]) -> Dict[str, Any]
def posterior_split_half_stability(bets: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def n_required_independent_bets(p0: float=0.5, p1: float=0.55, alpha: float=0.05, beta: float=0.2, delta: float=0.05) -> Dict[str, Any]
def nist_sample_size_table() -> List[Dict[str, Any]]
def evaluate_edge(trades: Sequence[Dict[str, Any]], trials_scanned: Optional[int]=None, choices: Optional[Dict[str, Any]]=None, periods: Optional[Sequence[Dict[str, Any]]]=None, context: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
def screen_universe(candidates: Sequence[Dict[str, Any]], trials_scanned: Optional[int]=None, choices: Optional[Dict[str, Any]]=None, periods_by_candidate: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
```

- `independent_bets` — Count INDEPENDENT bets, not raw trades.
- `time_disjoint_bets` — The maximum number of bets whose HOLDING INTERVALS do not overlap.
- `bet_outcomes` — One outcome per INDEPENDENT BET.
- `drawdown_duration` — The LONGEST underwater stretch, in observations and in days.
- `posterior_split_half_stability` — P(theta > 0.5) on the EARLY half versus the FULL history.
- `n_required_independent_bets` — The NIST-computed sample size for a claim about the win rate.
- `nist_sample_size_table` — The NIST sample sizes for a grid of claims, for reference.
- `evaluate_edge` — Judge a wallet's edge. Returns the metrics, the fluke tests, and a
- `screen_universe` — Screen a WHOLE universe of candidates and compute the PBO over it.

> **Gotcha.** The consistency gate. A wallet that scored FLUKE has not passed - the gate distinguishes a repeatable edge from one lucky trade, and all fifteen PEPE top-holder wallets have scored FLUKE.

---

<a id="gate_tests"></a>
## `gate_tests.py`

leapspace.gate_tests - the individual consistency-gate tests.

*286 lines · 1 public functions · 1 classes · layer: Validation*

**Depends on:** `pbo`

**Module constants:**

```python
DEFINITIVE = {'largest_win_share', 'skill_not_distinguishable', 'deflated_sharpe', 
INSUFFICIENT_ONLY = {'insufficient_independent_bets', 'single_token_only', 'too_few_closed
```

**Functions**

```python
def run_gate_tests(c: GateContext) -> Dict[str, Any]
```

- `run_gate_tests` — Run every consistency test and return the findings.

**Classes**

### `class GateContext`

Everything the individual tests need.

---

<a id="pbo"></a>
## `pbo.py`

Probability of Backtest Overfitting (PBO) and the multiple-testing
corrections that decide whether a "best of many" selection is a finding or
an artefact.

*718 lines · 5 public functions · 0 classes · layer: Validation*

**Functions**

```python
def probability_of_backtest_overfitting(candidate_returns: Sequence[Sequence[float]], n_splits: Optional[int]=None, n_partitions: int=8, test_fraction: float=0.5) -> Dict[str, Any]
def bonferroni_alpha(n_tests: int, family_alpha: float=0.05) -> float
def benjamini_hochberg(pvalues: Sequence[float], q: float=0.05) -> Dict[str, Any]
def multiple_testing_t_statistic_hurdle(n_tests: int, alpha: float=0.05) -> Dict[str, Any]
def harvey_liu_zhu_hurdle(n_tests: int, alpha: float=0.05) -> Dict[str, Any]
```

- `probability_of_backtest_overfitting` — Probability of Backtest Overfitting via CSCV.
- `bonferroni_alpha` — The per-test significance level that controls the family-wise error
- `benjamini_hochberg` — The Benjamini-Hochberg false-discovery-rate procedure.
- `multiple_testing_t_statistic_hurdle` — The Harvey-Liu-Zhu t-statistic hurdle for a newly discovered signal.
- `harvey_liu_zhu_hurdle` — Alias of `multiple_testing_t_statistic_hurdle` (same citation, same

> **Gotcha.** Probability of Backtest Overfitting. The CSCV combination count must be computed from the ACTUAL fold geometry; an empty return series silently yields a PBO of zero, which reads as a pass.

---

<a id="reference_gate"></a>
## `reference_gate.py`

An INDEPENDENT reference implementation of the memecoin consistency gate.

*1105 lines · 9 public functions · 0 classes · layer: Validation*

**Module constants:**

```python
_ND = NormalDist()
_EULER_GAMMA = 0.5772156649015329
```

**Functions**

```python
def bet_structure(trades: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]
def independent_bets(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def time_disjoint_bets(trades: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def wilson_interval(wins: int, n: int, confidence: float=0.95) -> Tuple[Optional[float], Optional[float]]
def binomial_tail_p(wins: int, n: int) -> Optional[float]
def expected_max_sharpe(n_trials: int) -> float
def deflated_sharpe(sharpe: float, n_obs: int, n_trials: int, skew: float=0.0, kurtosis: float=3.0) -> Optional[float]
def nist_sample_size(p0: float=0.5, p1: float=0.55, alpha: float=0.05, beta: float=0.2, delta: float=0.05) -> Dict[str, Any]
def evaluate(trades: Sequence[Dict[str, Any]], trials_scanned: Optional[int]=None, choices: Optional[Dict[str, Any]]=None, periods: Optional[Sequence[Dict[str, Any]]]=None, context: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
```

- `bet_structure` — One outcome per INDEPENDENT BET, with the time-disjoint flag.
- `independent_bets` — Count the INDEPENDENT BETS, with per-asset detail.
- `time_disjoint_bets` — The maximum set of mutually NON-OVERLAPPING holding intervals.
- `wilson_interval` — The Wilson score interval for a win rate. Returns (lower, upper).
- `binomial_tail_p` — P(the true win rate exceeds 50%) under a uniform Beta(1,1) prior.
- `expected_max_sharpe` — SR0: the expected maximum Sharpe over N independent trials.
- `deflated_sharpe` — The Deflated Sharpe Ratio, per Bailey & Lopez de Prado Eq. (2).
- `nist_sample_size` — The NIST sample size for a win-rate claim. Reported BESIDE the
- `evaluate` — Judge a wallet's edge. Returns the metrics, the fluke tests and a

---

# Reports & visualisation

_Markdown, JSON, inline-SVG dashboards_

<a id="backtestviz"></a>
## `backtestviz.py`

The backtest outcome visualisation: equity, drawdown, and the P&L shape.

*899 lines · 4 public functions · 0 classes · layer: Reports & visualisation*

**Depends on:** `viz_leading`

**Module constants:**

```python
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTCOMES_PATH = os.path.join(ROOT, 'reports', 'backtest_outcomes.json')
DASHBOARD_PATH = os.path.join(ROOT, 'reports', 'charts', 'backtest_outcomes.html')
```

**Functions**

```python
def collect_outcomes(results_path: Optional[str]=None, scorecard_paths: Optional[Sequence[str]]=None) -> Dict[str, Any]
def outcome_statistics(rets: Sequence[float]) -> Dict[str, Any]
def render_backtest_dashboard(data: Dict[str, Any]) -> str
def build_backtest_dashboard(results_path: Optional[str]=None, scorecard_paths: Optional[Sequence[str]]=None, out_path: Optional[str]=None, json_path: Optional[str]=None) -> Dict[str, Any]
```

- `collect_outcomes` — Gather the outcome data for every spec that has any.
- `outcome_statistics` — The shape of the out-of-sample P&L.
- `render_backtest_dashboard` — Render the outcomes dashboard.
- `build_backtest_dashboard` — Collect the outcomes and render the dashboard.

> **Gotcha.** The OOS return series come from the RAW SCORECARDS, not the results file - the results file never carried them. The paths are downsampled for rendering, keeping the first and last exactly, because a 4,290-bar polyline per series made a megabyte of SVG for no visual gain.

---

<a id="paperreport"></a>
## `paperreport.py`

The paper-concept report: the matrix, read and rendered.

*953 lines · 5 public functions · 0 classes · layer: Reports & visualisation*

**Depends on:** `viz_leading`

**Module constants:**

```python
PAPER_REPORT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)
_HTML_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)
_VERDICT_COLOUR = {'SUPPORTED': UP, 'FRAGILE': WARN, 'REFUTED': DOWN, 'INCONCLUSIVE': NE
```

**Functions**

```python
def load_results(path: Optional[str]=None) -> List[Dict[str, Any]]
def summarise(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]
def render_markdown(rows: Sequence[Dict[str, Any]], summary: Optional[Dict[str, Any]]=None) -> str
def render_html(rows: Sequence[Dict[str, Any]], summary: Optional[Dict[str, Any]]=None) -> str
def build_report(results_path: Optional[str]=None, md_path: Optional[str]=None, html_path: Optional[str]=None) -> Dict[str, Any]
```

- `load_results` — The results rows, or an empty list when there are none.
- `summarise` — Turn the rows into the tables the report renders.
- `render_markdown` — Render the findings as markdown.
- `render_html` — Render the matrix as a self-contained HTML page.
- `build_report` — Build the markdown report and the HTML dashboard.

> **Gotcha.** The report separates a FINDING from a CRASH. A spec whose signal never fired produced zero trades and a null Sharpe; that is a real result, not a crash, and the detector distinguishes them by the presence of an `errors` entry.

---

<a id="report"></a>
## `report.py`

Consolidated report writer.

*396 lines · 3 public functions · 0 classes · layer: Reports & visualisation*

**Depends on:** `provenance`, `reportvalidate`, `source_reliability`

**Module constants:**

```python
REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)
```

**Functions**

```python
def merge_full_gauntlet(payload: Dict[str, Any], path: str) -> int
def render_report(payload: Dict[str, Any]) -> str
def write_report(payload: Dict[str, Any], out_dir: str=REPORT_DIR) -> Dict[str, str]
```

- `merge_full_gauntlet` — Overlay the FULL-gauntlet verdicts onto a quick-run payload.

---

<a id="report_memecoin"></a>
## `report_memecoin.py`

The MEMECOIN-TRADER half of the consolidated report.

*2508 lines · 4 public functions · 0 classes · layer: Reports & visualisation*

**Depends on:** `etherscan`

**Module constants:**

```python
LIVE = 'LIVE'
SYNTHETIC = 'SYNTHETIC'
DERIVED = 'DERIVED-FROM-ARTEFACT'
ALLOWED_PROVENANCE = (LIVE, SYNTHETIC, DERIVED)
WHITELIST_STATUSES = ('WHITELISTED', 'WATCH', 'FLUKE', 'RETIRED')
ENFORCEMENT_MODULES = ('edge.py', 'pbo.py', 'traders.py', 'priced.py')
```

**Functions**

```python
def build_memecoin_sections(package_root: Optional[str]=None) -> Dict[str, Any]
def render_memecoin_markdown(payload: Dict[str, Any]) -> str
def write_memecoin_report(payload: Optional[Dict[str, Any]]=None, package_root: Optional[str]=None, out_dir: Optional[str]=None) -> Dict[str, str]
def main() -> int
```

- `build_memecoin_sections` — Build the machine-readable memecoin-trader payload.
- `render_memecoin_markdown` — Render the memecoin-trader payload as markdown.
- `write_memecoin_report` — Write reports/memecoin_report.md and reports/memecoin_report.json.
- `main` — Render the report and write both artefacts.

---

<a id="viz"></a>
## `viz.py`

Visual presentation of the package's outputs.

*789 lines · 10 public functions · 0 classes · layer: Reports & visualisation*

**Depends on:** `backtest`, `chains`, `friction`, `models`, `report`, `report_memecoin`

**Module constants:**

```python
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'report
REPORT_DIR = os.path.abspath(REPORT_DIR)
VIZ_DIR = os.path.join(REPORT_DIR, 'charts')
UP = '#00ff88'
DOWN = '#ff4444'
NEUTRAL = '#4488ff'
WARN = '#ffaa00'
MA_SHORT = '#ff6600'
MA_LONG = '#3399ff'
BG = '#1a1a2e'
GRID = '#333333'
TEXT = '#e0e0e0'
# ... and 2 more
```

**Functions**

```python
def load_backtest_results(path: Optional[str]=None) -> List[Dict[str, Any]]
def equity_curve_for_spec(spec: Dict[str, Any]) -> Dict[str, Any]
def chart_verdicts(rows: List[Dict[str, Any]], path: str) -> Optional[str]
def chart_walk_forward(rows: List[Dict[str, Any]], path: str) -> Optional[str]
def chart_equity(equities: Dict[str, List[float]], path: str, title: str='Equity curves (real engine output)') -> Optional[str]
def chart_simulation(sim: Dict[str, Any], path: str) -> Optional[str]
def chart_regime(price: Sequence[float], labels: Sequence[str], path: str, title: str='Market regime') -> Optional[str]
def chart_chains(health: Dict[str, Any], path: str) -> Optional[str]
def run_demo_simulation(seed: int=42) -> Any
def build_dashboard(out_dir: str=VIZ_DIR, results_path: Optional[str]=None, live: bool=True) -> Dict[str, Any]
```

- `equity_curve_for_spec` — Run one spec through the engine and capture its real equity curve.
- `chart_verdicts` — IS Sharpe vs OOS Sharpe for every spec, coloured by verdict.
- `chart_walk_forward` — Per-fold in-sample vs out-of-sample Sharpe.
- `chart_equity` — Equity curve above, underwater drawdown below, shared x-axis.
- `chart_simulation` — The friction-aware copy-trade simulation: equity, drawdown, rugs.
- `chart_regime` — Price with the HMM regime states shaded behind it.
- `chart_chains` — Multi-chain reachability and live liquidity.
- `run_demo_simulation` — Run the friction-aware copy-trade simulation for the dashboard.
- `build_dashboard` — Build the PNG charts and the HTML dashboard. Returns the paths.

---

<a id="viz_leading"></a>
## `viz_leading.py`

Visual presentation of the LEADING-indicator work.

*474 lines · 4 public functions · 0 classes · layer: Reports & visualisation*

**Module constants:**

```python
UP = '#00ff88'
DOWN = '#ff4444'
NEUTRAL = '#4488ff'
WARN = '#ffaa00'
BG = '#1a1a2e'
GRID = '#333333'
TEXT = '#e0e0e0'
MUTED = '#aaaaaa'
ACCENT = '#ffcc00'
_LEADING_VIZ_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)
_PAGE = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n<meta 
```

**Functions**

```python
def svg_line_chart(series: Sequence[Dict[str, Any]], labels: Optional[Sequence[str]]=None, title: str='', width: int=1000, height: int=320, y_label: str='', hlines: Sequence[Dict[str, Any]]=(), legend: bool=True) -> str
def svg_bars(items: Sequence[Dict[str, Any]], title: str='', width: int=1000, height: int=260, value_key: str='value', label_key: str='label') -> str
def render_leading_dashboard(payload: Dict[str, Any]) -> str
def build_leading_dashboard(payload: Dict[str, Any], out_dir: Optional[str]=None) -> Dict[str, Any]
```

- `svg_line_chart` — Render one or more line series as inline SVG.
- `svg_bars` — Render a labelled bar chart as inline SVG (used for GEX by expiry).
- `render_leading_dashboard` — Render the whole leading-indicator page as one HTML string.
- `build_leading_dashboard` — Write the leading-indicator dashboard. Returns the paths written.

---

<a id="viz_memecoin"></a>
## `viz_memecoin.py`

Charts for the memecoin-trader half of the package.

*346 lines · 5 public functions · 0 classes · layer: Reports & visualisation*

**Depends on:** `viz`

**Module constants:**

```python
BG = '#1a1a2e'
FG = '#e8e8e8'
MUTED = '#9aa0b4'
GREEN = '#2ecc71'
RED = '#e74c3c'
BLUE = '#3498db'
AMBER = '#f39c12'
PURPLE = '#9b59b6'
GRID = '#2a2a44'
VERDICT_COLOR = {'CONSISTENT': GREEN, 'WEAK': AMBER, 'FLUKE': RED, 'INSUFFICIENT': MUT
```

**Functions**

```python
def chart_edge_gate(results: Sequence[Dict[str, Any]], path: str) -> Optional[str]
def chart_whitelist(wl: Dict[str, Any], path: str) -> Optional[str]
def chart_price_accuracy(path: str) -> Optional[str]
def chart_criteria_coverage(rows: Sequence[Dict[str, Any]], path: str) -> Optional[str]
def chart_community_series(series_by_token: Dict[str, Any], path: str) -> Optional[str]
```

- `chart_edge_gate` — The key chart: raw closed trades vs INDEPENDENT BETS, per wallet.
- `chart_whitelist` — Whitelist status counts and the promotion/retirement timeline.
- `chart_price_accuracy` — The price-at-block method against the known reference prices.
- `chart_criteria_coverage` — Which of the cited criteria are actually enforced in code.
- `chart_community_series` — The community-size series as it accrues.

---

# Governance & policy

_Kill switch, disclosure, source reliability, readiness_

<a id="alerts"></a>
## `alerts.py`

Alerts — price, information and action — derived from the research papers.

*753 lines · 7 public functions · 2 classes · layer: Governance & policy*

**Depends on:** `provenance`

**Functions**

```python
def price_alerts_from_bars(symbol: str, bars: Sequence[Dict[str, Any]], provenance: str='') -> List[Alert]
def regime_transition_alerts(regime_result: Any, symbol: str='MARKET', provenance: str='') -> List[Alert]
def gamma_alerts(gamma: Any, flow: Any=None, provenance: str='') -> List[Alert]
def disclosure_alerts(disclosure_report: Dict[str, Any], assets_by_filing: Optional[Dict[str, List[Dict[str, Any]]]]=None, provenance: str='') -> List[Alert]
def onchain_alerts(wallet_profiles: Sequence[Any], concentration: Optional[Dict[str, Any]]=None, provenance: str='') -> List[Alert]
def memecoin_alerts(screen: Dict[str, Any], provenance: str='') -> List[Alert]
def action_alerts(regime_result: Any=None, gamma: Any=None, flow: Any=None, symbol: str='MARKET', provenance: str='') -> List[Alert]
```

- `price_alerts_from_bars` — Drawdown and volatility-expansion alerts from real OHLCV.
- `regime_transition_alerts` — Alert on a regime STATE CHANGE, with the posterior probabilities.
- `gamma_alerts` — Gamma-state and option-flow pressure alerts.
- `disclosure_alerts` — Alerts from US officials' disclosures, all three branches.
- `onchain_alerts` — Alerts from wallet behaviour and holder concentration.
- `memecoin_alerts` — Alerts from a meme-coin screen result.
- `action_alerts` — The ACTION layer: what the papers say to DO, given the current state.

**Classes**

### `class Alert`

```python
def fingerprint(self) -> str
def to_dict(self) -> Dict[str, Any]
def render(self) -> str
```


### `class AlertEngine`

Collects alerts, suppresses repeats against a state file, renders.

```python
def add(self, alerts: Sequence[Alert]) -> None
def add_gap(self, gap: Dict[str, Any]) -> None
def new_alerts(self) -> List[Alert]
def render(self, only_new: bool=True, show_thresholds: bool=True) -> str
def save_state(self) -> Optional[str]
def to_dict(self) -> Dict[str, Any]
```

- `new_alerts` — Alerts not seen in a previous run.

---

<a id="signal"></a>
## `signal.py`

leapspace.signal - the trade-decision engine.

*1269 lines · 14 public functions · 2 classes · layer: Governance & policy*

**Depends on:** `riskguard`

**Module constants:**

```python
UNAVAILABLE = 'UNAVAILABLE'
ENTER = 'ENTER'
WATCH = 'WATCH'
AVOID = 'AVOID'
NO_DATA = 'NO_TRADE_DATA'
SUPPORTS = 'SUPPORTS'
CONFLICTS = 'CONFLICTS'
NEUTRAL = 'NEUTRAL'
_SUPPLY_HOSTS = {'ethereum': 'https://eth.blockscout.com', 'base': 'https://base.block
```

**Functions**

```python
def leg_identity(address: str, chain: str='solana') -> Leg
def leg_data_quality(legs: List[Leg]) -> Leg
def leg_research_edge(project_root: Optional[str]=None) -> Leg
def leg_qualified_wallets(token_address: str, project_root: Optional[str]=None) -> Leg
def leg_narrative(address: str, chain: str='solana') -> Leg
def leg_traction(address: str, chain: str='solana') -> Leg
def leg_holder_risk(address: str, chain: str='solana') -> Leg
def leg_liquidity(identity: Leg, target_usd: float=1000.0) -> Leg
def kill_switch_gate(ks: Any=None, token_address: Optional[str]=None, chain: str='ethereum', equity_usd: Optional[float]=None, liquidity_usd: Optional[float]=None, slippage_bps: Optional[float]=None, ts: Optional[int]=None, project_root: Optional[str]=None) -> Dict[str, Any]
def halt_on_data_quality(ks: Any, dq_leg: Optional['Leg']=None) -> bool
def apply_kill_switch(signal_obj: Dict[str, Any], gate: Dict[str, Any]) -> Dict[str, Any]
def assess_trade(address: str, chain: str='solana', target_usd: float=1000.0, project_root: Optional[str]=None, risk_per_trade_pct: float=0.005, max_position_pct_of_liquidity: float=0.01) -> TradeSignal
def render_brief(sig: TradeSignal) -> str
def write_brief(sig: TradeSignal, path: str) -> str
```

- `leg_identity` — Resolve the token and its current market state from live DEX data.
- `leg_data_quality` — Grade how much of the evidence set actually answered.
- `leg_research_edge` — What do the paper-derived specifications currently say?
- `leg_qualified_wallets` — How many QUALIFIED wallets hold this token, and what did they do?
- `leg_narrative` — Narrative specificity: does the project declare a specific story?
- `leg_traction` — Traction: observable market and community behaviour.
- `leg_holder_risk` — Concentration and insider share of the holder base.
- `leg_liquidity` — Is there enough depth to enter AND exit a target position?
- `kill_switch_gate` — Ask the kill switch whether trading is permitted right now.
- `halt_on_data_quality` — Halt the switch when the evidence set is too thin to trade on.
- `apply_kill_switch` — Apply the gate's answer to a verdict.
- `assess_trade` — Gather every leg of evidence and return a decision.
- `render_brief` — Render the decision as a briefing the user can act on.

**Classes**

### `class Leg`

One independent strand of evidence.

### `class TradeSignal`

```python
def to_dict(self) -> Dict[str, Any]
```


> **Gotcha.** `assess_trade` consults the persisted kill switch and downgrades an ENTER to an AVOID. There is NO order-placement path anywhere in the package, so the brake cannot yet stop a real order - it gates a decision, not a trade.

---

# Wallet & chain profiling

_Holder analysis, wallet search, consistency gates_

<a id="launchscan"></a>
## `launchscan.py`

Launch scan: identify early buyers of a NEW memecoin and test whether
they are already-consistent traders.

*628 lines · 7 public functions · 0 classes · layer: Wallet & chain profiling*

**Depends on:** `costs`, `edge`, `http`, `memecoinscan`, `provenance`

**Module constants:**

```python
BLOCKSCOUT_HOSTS = {'ethereum': 'https://eth.blockscout.com'}
EVM_RPC = 'https://ethereum-rpc.publicnode.com'
TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ZERO_ADDRESS = '0x' + '0' * 40
```

**Functions**

```python
def fetch_transfer_logs(token: str, from_block: int, to_block: int, chain: str='ethereum', max_providers: int=4) -> Dict[str, Any]
def decode_transfer_logs(logs: List[Dict[str, Any]], decimals: int=18) -> List[Dict[str, Any]]
def scan_launch_window(logs: List[Dict[str, Any]], launch_block: int, window_blocks: int=1000, decimals: int=18, provider: Optional[str]=None, token: Optional[str]=None) -> Dict[str, Any]
def token_launch(token: str, chain: str='ethereum') -> Dict[str, Any]
def fetch_token_transfers(token: str, chain: str='ethereum', max_pages: int=40) -> Dict[str, Any]
def early_buyers(token: str, chain: str='ethereum', window_blocks: int=1000, max_pages: int=40) -> Dict[str, Any]
def screen_early_buyers(token: str, chain: str='ethereum', window_blocks: int=1000, universe: Optional[Dict[str, Any]]=None, max_candidates: int=25, max_pages: int=40, early: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
```

- `fetch_transfer_logs` — Fetch a token's ERC-20 Transfer LOGS over a block range.
- `decode_transfer_logs` — Decode ERC-20 Transfer logs into per-recipient purchases.
- `scan_launch_window` — Find the buyers inside a launch window, from transfer logs.
- `token_launch` — The launch block and creation transaction of a token.
- `fetch_token_transfers` — ALL transfers of a token, paginated.
- `early_buyers` — Wallets that bought the token within `window_blocks` of its launch.
- `screen_early_buyers` — Find early buyers of a token and test each against the edge gate.

> **Gotcha.** The launch window is found with a BOUNDED `eth_getLogs` query over `[launch_block, launch_block + window]`, not by paging an established token's whole history. Public RPC providers can return DIFFERENT SUBSETS of the same range, so provider provenance is recorded and subsets are never merged.

---

<a id="memecoin"></a>
## `memecoin.py`

Meme-coin screening — the paper's five-layer edge framework.

*779 lines · 5 public functions · 1 classes · layer: Wallet & chain profiling*

**Depends on:** `http`, `market`, `narrative`, `provenance`

**Module constants:**

```python
JUPITER_TOKEN = 'https://lite-api.jup.ag/tokens/v2/search?query={mint}'
RUGCHECK_REPORT = 'https://api.rugcheck.xyz/v1/tokens/{mint}/report'
THRESHOLDS = {'min_liquidity_usd': 25000.0, 'min_volume_24h_usd': 50000.0, 'max_top
MAJOR_DEXES = {'raydium', 'raydium-clmm', 'orca', 'meteora', 'meteoraDlmm', 'meteora
LAUNCHPAD_DEXES = {'pumpswap', 'raydiumlaunchlab', 'raydium-launchlab', 'launchlab', 'be
```

**Functions**

```python
def fetch_token_profile(mint: str) -> Tuple[Dict[str, Any], Provenance]
def fetch_rugcheck(mint: str) -> Tuple[Dict[str, Any], Provenance]
def fetch_migration_evidence(mint: str) -> Tuple[Dict[str, Any], Provenance]
def screen_meme_coin(mint: str, pair: Optional[Dict[str, Any]]=None, thresholds: Optional[Dict[str, float]]=None) -> ScreenResult
def screen_search(query: str, limit: int=15, thresholds: Optional[Dict[str, float]]=None) -> Dict[str, Any]
```

- `fetch_token_profile` — Jupiter token profile: holder count, authorities, organic score, audit.
- `fetch_rugcheck` — RugCheck full report: top holders with insider flags, risks, liquidity.
- `fetch_migration_evidence` — Launchpad-origin and migration evidence from the token's DEX pairs.
- `screen_meme_coin` — Apply the paper's five layers to one token.
- `screen_search` — Search a meme-coin narrative and screen each result.

**Classes**

### `class ScreenResult`

```python
def to_dict(self) -> Dict[str, Any]
```


> **Gotcha.** The memecoin screen. Prices are taken AT THE BLOCK, so a token that moved after the wallet bought it is not scored on a price the wallet never saw.

---

<a id="memecoinscan"></a>
## `memecoinscan.py`

Reverse-engineer the trading process of PEPE's top holders.

*771 lines · 5 public functions · 0 classes · layer: Wallet & chain profiling*

**Depends on:** `etherscan`, `http`, `provenance`

**Module constants:**

```python
BLOCKSCOUT = {'ethereum': 'https://eth.blockscout.com'}
MEME_SYMBOLS = ['PEPE', 'SHIB', 'FLOKI', 'WIF', 'BONK', 'MOG', 'POPCAT', 'BRETT', 'TU
MIN_LIQUIDITY_USD = 50000.0
EVM_RPC = 'https://ethereum-rpc.publicnode.com'
NON_TRADER_ADDRESSES = {'0x0000000000000000000000000000000000000000', '0x00000000000000000000
```

**Functions**

```python
def fetch_top_holders(token: str, chain: str='ethereum', limit: int=50) -> Dict[str, Any]
def memecoin_universe(symbols: Optional[List[str]]=None, chain: str='ethereum') -> Dict[str, Any]
def fetch_token_transfers(address: str, chain: str='ethereum', max_items: int=400, token: Optional[str]=None) -> Dict[str, Any]
def token_launch_block(token: str, chain: str='ethereum') -> Dict[str, Any]
def wallet_memecoin_profile(address: str, universe: Dict[str, Any], chain: str='ethereum', max_items: int=400, known_exchange_addresses: Optional[Dict[str, str]]=None) -> Dict[str, Any]
```

- `fetch_top_holders` — Top holders of an ERC-20, with entity classification.
- `memecoin_universe` — Resolve meme symbols to live contract addresses via DexScreener.
- `fetch_token_transfers` — A wallet's ERC-20 transfer history from Blockscout.
- `token_launch_block` — The block a token was created in, and its creation timestamp.
- `wallet_memecoin_profile` — Reconstruct a wallet's memecoin allocation and trading process.

---

<a id="profiler"></a>
## `profiler.py`

Wallet profiling, anti-insider filtering, consensus and the trusted pool.

*680 lines · 6 public functions · 1 classes · layer: Wallet & chain profiling*

**Depends on:** `chains`, `models`, `provenance`

**Module constants:**

```python
POOL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state', 'tru
REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state', 'dep
```

**Functions**

```python
def load_registries(config: Optional[Dict[str, Any]]=None) -> Dict[str, List[str]]
def profile_wallet(chain: str, wallet: str, trades: Optional[Sequence[WalletTrade]]=None, thresholds: Optional[Dict[str, Any]]=None, source: str='', price_lookup: Optional[Any]=None) -> WalletProfile
def profile_many(chain: str, wallets: Sequence[str], thresholds: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
def trace_funding_source(chain: str, wallet: str, registries: Optional[Dict[str, List[str]]]=None) -> FundingSource
def is_insider(wallet: str, funding: FundingSource, registries: Optional[Dict[str, List[str]]]=None, launch_block: Optional[int]=None, snipe_block_window: int=5) -> Dict[str, Any]
def consensus_signal(trades: Sequence[WalletTrade], min_wallets: int=3, window_seconds: int=3600, trusted_wallets: Optional[Iterable[str]]=None, profiled_only: bool=True) -> Dict[str, Any]
```

- `load_registries` — The deployer / cabal / exchange / insider address lists.
- `profile_wallet` — Score one wallet against the operator's consistency thresholds.
- `profile_many` — Profile several wallets; returns a flat summary plus the raw profiles.
- `trace_funding_source` — Find the earliest inbound token transfer to a wallet.
- `is_insider` — Apply the anti-insider rules to one wallet.
- `consensus_signal` — Did >=N wallets act on the same token inside the window?

**Classes**

### `class TrustedPool`

The trusted wallet pool, with periodic re-evaluation.

```python
def load(self) -> bool
def save(self) -> str
def add(self, wallet: str, score: Optional[float]=None, reason: str='') -> None
def remove(self, wallet: str, reason: str='') -> None
def re_evaluate(self, profiles: Optional[Dict[str, Any]]=None) -> Dict[str, Any]
def to_flat(self) -> Dict[str, Any]
```

- `re_evaluate` — Demote wallets that no longer deserve to be trusted.

---

<a id="walletsearch"></a>
## `walletsearch.py`

leapspace.walletsearch - find wallets that are actually skilled.

*460 lines · 7 public functions · 0 classes · layer: Wallet & chain profiling*

**Module constants:**

```python
DEFAULT_SYMBOLS = ['PEPE', 'SHIB', 'DOGE', 'FLOKI', 'BONK', 'WIF', 'MOG', 'BRETT', 'POPC
```

**Functions**

```python
def build_universe(chain: str='ethereum', symbols: Optional[Sequence[str]]=None, extra_tokens: Optional[Sequence[Dict[str, Any]]]=None) -> Dict[str, Any]
def discover_new_tokens(chain: str='ethereum', limit: int=20, pages: int=2, progress: Optional[Any]=None) -> Dict[str, Any]
def discover_candidates(universe: Dict[str, Any], chain: str='ethereum', max_tokens: Optional[int]=None, holders_per_token: int=50, early_buyers: bool=True, early_window_blocks: int=1000, early_max_pages: int=40, progress: Optional[Any]=None) -> Dict[str, Any]
def screen_candidates(candidates: Sequence[Dict[str, Any]], universe: Dict[str, Any], chain: str='ethereum', trials_scanned: Optional[int]=None, max_candidates: int=25, progress: Optional[Any]=None) -> Dict[str, Any]
def search(chain: str='ethereum', symbols: Optional[Sequence[str]]=None, extra_tokens: Optional[Sequence[Dict[str, Any]]]=None, max_tokens: Optional[int]=None, min_breadth: int=2, max_candidates: int=25, holders_per_token: int=50, early_buyers: bool=True, progress: Optional[Any]=None) -> Dict[str, Any]
def render_report(result: Dict[str, Any]) -> str
def save(result: Dict[str, Any], path: str) -> str
```

- `build_universe` — A wide memecoin universe, resolved from live market data.
- `discover_new_tokens` — Find FRESH memecoins on a chain, from the chain's live top pools.
- `discover_candidates` — Find candidate wallets across the universe and score their BREADTH.
- `screen_candidates` — Price and gate each candidate.
- `search` — The whole search: universe -> candidates -> screened -> ranked.
- `render_report` — A human-readable summary of a search.

---
