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

## Phase 2: Data Fetchers (Week 2)

**Goal**: Build tools to fetch raw market data from Hyperliquid API

### Tasks

- [ ] Implement `tools/ie_fetch_order_book.py`
  - [ ] Fetch L2 order book (top 20 levels)
  - [ ] Handle API errors gracefully
  - [ ] Add response caching (2-5 sec TTL)
  - [ ] Test with BTC, ETH, SOL

- [ ] Implement `tools/ie_fetch_funding.py`
  - [ ] Fetch current funding rate
  - [ ] Fetch 24h funding history
  - [ ] Test with multiple coins

- [ ] Implement `tools/ie_fetch_open_interest.py`
  - [ ] Fetch current OI
  - [ ] Calculate OI changes (1h, 4h, 24h)
  - [ ] Test with real-time data

- [ ] Implement `ie/cache.py`
  - [ ] Time-based cache with TTL
  - [ ] LRU eviction for memory management
  - [ ] Cache hit rate logging

**Success Criteria**:
- All fetchers successfully retrieve data from Hyperliquid
- Proper error handling (timeouts, rate limits, network errors)
- Caching reduces API calls by 70%+

---

## Phase 3: Unified Metrics Tool (Week 3)

**Goal**: Create single agent-facing tool that combines all IE capabilities

### Tasks

- [ ] Implement `tools/ie_fetch_institutional_metrics.py`
  - [ ] Integrate all data fetchers
  - [ ] Call calculation functions
  - [ ] Return clean, structured metrics
  - [ ] Add configurable parameters (include_order_book, etc.)

- [ ] Enhance `tools/tool_fetch_hl_raw.py`
  - [ ] Add VWAP calculation to candle data
  - [ ] Add z-score calculation
  - [ ] Add volume ratio vs. 20-period average
  - [ ] Maintain backward compatibility

- [ ] Create output format documentation
- [ ] Test combined metrics on live data

**Success Criteria**:
- Single tool call returns all institutional metrics
- Data format is clean and agent-friendly
- Tool is registered and callable by LangChain agent
- Response time < 2 seconds (with caching)

---

## Phase 4: Agent Integration (Week 4)

**Goal**: Integrate IE metrics into agent workflow and context

### Tasks

- [ ] Create `agent_context/Quantitative_Metrics_Guide.md`
  - [ ] Explain each metric and how to use it
  - [ ] Provide examples of ICT + quant convergence
  - [ ] Define setup grading system (A+/A/B/C)

- [ ] Update `agent/agent.py`
  - [ ] Register `ie_fetch_institutional_metrics` tool
  - [ ] Update system prompt to include quant workflow
  - [ ] Add IE tools to agent toolset

- [ ] Update `requirements.txt`
  - [ ] Add numpy>=1.24.0
  - [ ] Add pandas>=2.0.0
  - [ ] Test dependency installation

- [ ] Update `config/settings.py`
  - [ ] Add IE configuration section
  - [ ] Add cache TTL settings
  - [ ] Add metric threshold configurations

**Success Criteria**:
- Agent can call IE tools successfully
- Agent references both ICT and quant metrics in responses
- System prompt guides agent to use both frameworks
- Setup grading (A+/A/B/C) works as expected

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

### Current Phase: **Phase 2** (Data Fetchers)
**Started**: 2025-11-08
**Status**: ⏳ Ready to Begin
**Completion**: 0%

### Phase Completion Summary

| Phase | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| Phase 1: IE Foundation | ✅ Complete | 2025-11-08 | 2025-11-08 | All tests passing |
| Phase 2: Data Fetchers | ⏳ Pending | - | - | Ready to start |
| Phase 3: Unified Metrics Tool | ⏳ Pending | - | - | - |
| Phase 4: Agent Integration | ⏳ Pending | - | - | - |
| Phase 5: Testing & Refinement | ⏳ Pending | - | - | - |

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
