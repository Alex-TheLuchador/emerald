# Institutional Engine (IE) Implementation Roadmap

**Project Goal**: Build a data infrastructure layer that fetches and calculates institutional-grade quantitative metrics for the AI agent to use in trading strategy.

**Timeline**: 4-6 weeks
**Status**: 🚧 In Progress

---

## Overview

The Institutional Engine (IE) is a **data + calculation layer** that provides quantitative metrics to the AI agent. The agent remains responsible for all strategic decision-making, combining these metrics with existing ICT analysis.

```
AI Agent (Strategy) → IE Tools (Data) → Hyperliquid API
```

---

## Phase 1: IE Foundation (Week 1) ✅ COMPLETE

**Goal**: Set up IE infrastructure and core calculation utilities

### Tasks

- [x] Create IE roadmap document
- [x] Create `ie/` directory structure
- [x] Implement `ie/data_models.py` (data structures)
- [x] Implement `ie/calculations.py` (pure math functions)
  - [x] `calculate_order_book_imbalance()`
  - [x] `calculate_vwap()`
  - [x] `calculate_z_score()`
  - [x] `calculate_funding_annualized()`
  - [x] `calculate_oi_change()`
  - [x] `calculate_volume_ratio()`
- [x] Create unit tests for calculations
- [x] Document each calculation function

**Success Criteria**: ✅ ALL MET
- ✅ All calculation functions tested with sample data
- ✅ Functions return correct outputs for known inputs
- ✅ Code is clean, documented, and type-hinted

**Completed**: 2025-11-08

---

## Phase 2: Data Fetchers (Week 2) ✅ COMPLETE

**Goal**: Build tools to fetch raw market data from Hyperliquid API

### Tasks

- [x] Implement `tools/ie_fetch_order_book.py`
  - [x] Fetch L2 order book (top 20 levels)
  - [x] Handle API errors gracefully
  - [x] Add response caching (2 sec TTL)
  - [x] LangChain tool wrapper

- [x] Implement `tools/ie_fetch_funding.py`
  - [x] Fetch current funding rate
  - [x] Fetch 24h funding history
  - [x] Funding trend analysis
  - [x] LangChain tool wrapper

- [x] Implement `tools/ie_fetch_open_interest.py`
  - [x] Fetch current OI
  - [x] Calculate OI changes (1h, 4h, 24h)
  - [x] Price-OI divergence detection
  - [x] Historical OI tracking (JSON file)
  - [x] LangChain tool wrapper

- [x] Implement `ie/cache.py`
  - [x] Time-based cache with TTL
  - [x] Thread-safe operations
  - [x] Cache hit rate tracking
  - [x] Statistics monitoring

**Success Criteria**: ✅ ALL MET
- ✅ All fetchers implemented with proper structure
- ✅ Comprehensive error handling (403, timeouts, parsing errors)
- ✅ Caching system working (verified in tests)
- ✅ Tool wrappers ready for LangChain integration

**Completed**: 2025-11-08

**Note**: Live API testing blocked by 403 Forbidden (IP restrictions in test environment). Code structure validated, error handling confirmed working. Will test with real API access in production environment.

---

## Phase 3: Unified Metrics Tool (Week 3) ✅ COMPLETE

**Goal**: Create single agent-facing tool that combines all IE capabilities

### Tasks

- [x] Implement `tools/ie_fetch_institutional_metrics.py`
  - [x] Integrate all data fetchers
  - [x] Call calculation functions
  - [x] Return clean, structured metrics
  - [x] Add configurable parameters (include_order_book, etc.)
  - [x] Generate summary with convergence analysis
  - [x] Provide trade recommendations based on signal strength

- [x] Enhance `tools/tool_fetch_hl_raw.py`
  - [x] Add VWAP calculation to candle data
  - [x] Add z-score calculation
  - [x] Add volume ratio vs. 20-period average
  - [x] Add VWAP bands (similar to Bollinger Bands)
  - [x] Maintain backward compatibility (include_vwap parameter)

- [x] Create usage documentation and demos
  - [x] Created comprehensive demo script (demo_ie_usage.py)
  - [x] 4 interactive demos showing all features
  - [x] Examples of ICT + IE convergence analysis

- [x] Test combined metrics

**Success Criteria**: ✅ ALL MET
- ✅ Single tool call returns all institutional metrics
- ✅ Data format is clean and agent-friendly
- ✅ Tool wrappers ready for LangChain agent
- ✅ Convergence scoring system implemented
- ✅ Setup grading system (A+/A/B/C) defined
- ✅ Demo script shows agent workflow

**Completed**: 2025-11-08

---

## Phase 4: Agent Integration (Week 4) ✅ COMPLETE

**Goal**: Integrate IE metrics into agent workflow and context

### Tasks

- [x] Create `agent_context/Quantitative_Metrics_Guide.md`
  - [x] Explain each metric and how to use it
  - [x] Provide examples of ICT + quant convergence
  - [x] Define setup grading system (A+/A/B/C)
  - [x] Include analysis workflow instructions
  - [x] Show expected response format

- [x] Update `agent/agent.py`
  - [x] Import `fetch_institutional_metrics_tool`
  - [x] Register IE tool with agent
  - [x] Update system prompt with IE workflow
  - [x] Add tool usage instructions
  - [x] Update mission statement

- [x] Update `requirements.txt`
  - [x] No changes needed (IE uses pure Python, no external deps)

- [x] Update `config/settings.py`
  - [x] Add IE configuration dataclass
  - [x] Add cache TTL settings (order book: 2s, funding/OI: 5min)
  - [x] Add metric threshold configurations
  - [x] Add convergence scoring weights
  - [x] Add setup grading thresholds

- [x] Create test script
  - [x] Test agent with ICT only
  - [x] Test agent with ICT + IE
  - [x] Test agent with IE direct
  - [x] Show expected workflow

**Success Criteria**: ✅ ALL MET
- ✅ Agent can call IE tools successfully
- ✅ Agent has access to both fetch_hl_raw and fetch_institutional_metrics_tool
- ✅ System prompt guides hybrid analysis workflow
- ✅ Setup grading system integrated
- ✅ Quantitative Metrics Guide loaded automatically as context
- ✅ Test script demonstrates full integration

**Completed**: 2025-11-08

---

## Phase 5: Testing & Refinement (Week 5-6)

**Goal**: Validate IE metrics, optimize performance, refine thresholds

### Tasks

- [ ] End-to-end testing
  - [ ] Test multiple coins (BTC, ETH, SOL, ARB)
  - [ ] Test across different market conditions
  - [ ] Test with real agent queries

- [ ] Performance optimization
  - [ ] Profile API call times
  - [ ] Optimize caching strategy
  - [ ] Reduce redundant calculations

- [ ] Threshold calibration
  - [ ] Test order book imbalance thresholds
  - [ ] Test VWAP z-score extremes
  - [ ] Test funding rate extremes
  - [ ] Adjust based on real market data

- [ ] Documentation
  - [ ] Update README with IE section
  - [ ] Create IE developer documentation
  - [ ] Add usage examples
  - [ ] Document API rate limits and caching strategy

- [ ] Error handling & edge cases
  - [ ] Handle missing data gracefully
  - [ ] Handle API outages
  - [ ] Handle extreme market conditions
  - [ ] Add comprehensive logging

**Success Criteria**:
- Agent successfully analyzes setups using both ICT + IE metrics
- Response time acceptable (< 3 seconds total)
- No errors with common use cases
- Metric thresholds validated against real market data
- Documentation complete and clear

---

## Future Enhancements (Post-Launch)

### Optional Advanced Features

- [ ] **Historical data storage** (SQLite database)
  - Store IE metrics over time
  - Enable trend analysis
  - Support backtesting

- [ ] **Backtesting framework**
  - Test ICT + IE setups on historical data
  - Track performance metrics
  - Optimize metric thresholds

- [ ] **Multi-exchange support**
  - Expand beyond Hyperliquid
  - Compare metrics across exchanges
  - Identify arbitrage opportunities

- [ ] **Advanced metrics**
  - Delta volume analysis
  - Liquidation heatmaps
  - Whale wallet tracking
  - On-chain metrics integration

- [ ] **Alert system**
  - Notify when extreme metrics detected
  - Discord/Telegram integration
  - Customizable alert thresholds

- [ ] **Visual dashboard**
  - Web UI for IE metrics
  - Real-time metric display
  - Historical charts

---

## Progress Tracking

### Current Phase: **Phase 5** (Testing & Refinement)
**Started**: Not yet started
**Status**: ⏳ Ready to Begin
**Completion**: 0%

### Phase Completion Summary

| Phase | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| Phase 1: IE Foundation | ✅ Complete | 2025-11-08 | 2025-11-08 | All tests passing |
| Phase 2: Data Fetchers | ✅ Complete | 2025-11-08 | 2025-11-08 | All 3 fetchers + cache done |
| Phase 3: Unified Metrics Tool | ✅ Complete | 2025-11-08 | 2025-11-08 | Unified tool + VWAP enhancement |
| Phase 4: Agent Integration | ✅ Complete | 2025-11-08 | 2025-11-08 | Agent fully integrated |
| Phase 5: Testing & Refinement | ⏳ Pending | - | - | Ready to start |

---

## Key Decisions & Design Choices

### ✅ Confirmed Decisions

1. **IE is data-only**: No strategy logic in IE layer - agent handles all strategy
2. **Unified tool approach**: Single `fetch_institutional_metrics` tool vs. separate tools
3. **Hybrid ICT + Quant**: Preserve existing ICT framework, add quant validation
4. **Setup grading system**: A+/A/B/C based on convergence of metrics
5. **Caching strategy**: 2-5 min TTL for different data types

### ⏸️ Decisions Pending

1. Which exchange APIs to support (starting with Hyperliquid only)
2. Historical data storage strategy (defer to post-launch)
3. Backtesting framework scope (defer to post-launch)
4. Alert system integration (defer to post-launch)

---

## Dependencies

### Current
- anthropic>=0.18.0
- langchain>=0.1.0
- langchain-anthropic>=0.1.0
- python-dotenv>=1.0.0
- requests>=2.31.0
- rich>=13.0.0

### To Add (Phase 4)
- numpy>=1.24.0
- pandas>=2.0.0

---

## Notes & Learnings

*This section will be updated as we progress with insights, challenges, and solutions.*

### 2025-11-08
- Started IE implementation
- Confirmed hybrid approach (ICT + Quantitative)
- IE designed as pure data/calculation layer
- Agent retains full strategic control

**Phase 1 Completion:**
- Implemented 6 core calculation functions (order book imbalance, VWAP, z-score, funding, OI, volume)
- Created comprehensive data models using Python dataclasses
- All 8 test cases passing successfully
- Functions are pure, type-hinted, and well-documented
- Ready to proceed with Phase 2 (API fetchers)

**Phase 2 Completion:**
- Implemented 3 data fetchers (order book, funding, open interest)
- Built thread-safe caching system with TTL
- All fetchers have proper error handling and LangChain tool wrappers
- Created comprehensive test suite
- Historical OI tracking implemented (JSON file storage)
- Each fetcher uses IE calculation functions from Phase 1
- Ready to proceed with Phase 3 (unified metrics tool)

**Phase 3 Completion:**
- Created unified `fetch_institutional_metrics` tool (one call gets everything)
- Implemented convergence scoring system (0-100 scale)
- Built setup grading system (A+/A/B/C based on signal convergence)
- Enhanced `fetch_hl_raw` with VWAP analysis (backward compatible)
- VWAP metrics: price, z-score, deviation level, bands, volume ratio
- Created comprehensive demo script with 4 interactive examples
- Shows ICT + IE convergence workflow
- Ready to proceed with Phase 4 (agent integration)

**Phase 4 Completion:**
- Created Quantitative Metrics Guide context document (comprehensive)
- Agent now has 2 tools: fetch_hl_raw + fetch_institutional_metrics_tool
- Updated system prompt with IE workflow instructions
- Added IE configuration to settings.py (all thresholds configurable)
- Agent automatically loads Quantitative Metrics Guide as context
- Setup grading system (A+/A/B/C) integrated into agent behavior
- Created test_agent_with_ie.py to demonstrate integration
- No external dependencies needed (pure Python calculations)
- Agent ready for Phase 5 (testing with real data)

**Bugfix - API Response Format Handling:**
- Fixed all 3 IE fetchers to handle actual Hyperliquid API response format
- Order book parser: Added support for direct list format ([bids, asks])
- Funding parser: Added multiple field name checks (funding, fundingRate, funding_rate, prevFunding)
- OI parser: Added multiple field name checks for coin, OI, and price fields
- All parsers now case-insensitive and handle coin name variations (e.g., "BTC" vs "BTC-USD")
- Improved type checking in all parsers (isinstance checks before .get() calls)
- Ready for real API testing

---

## Questions & Issues

*Track blockers and open questions here*

### Open Questions
- [ ] What are Hyperliquid's API rate limits?
- [ ] Should we support futures exchanges beyond Hyperliquid?
- [ ] How often should we recalculate VWAP (every candle vs. cached)?

### Resolved Questions
- ✅ Should IE include strategy logic? **No - agent only**
- ✅ Separate tools vs. unified tool? **Unified tool preferred**
- ✅ Keep ICT framework? **Yes - hybrid approach**

---

**Last Updated**: 2025-11-08
**Next Review**: After Phase 1 completion
