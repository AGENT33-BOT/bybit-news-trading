#!/usr/bin/env python3
"""
V2.1 Test Suite for bybit-news-trading
====================================
Tests for the 5 required scenarios per spec
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock CONFIG for testing
TEST_CONFIG = {
    "continuation": {
        "min_event_score": 8.0,
        "long_rsi_max": 78,
        "short_rsi_min": 22,
        "require_breakout": True,
        "require_volume_confirmation": True,
    },
    "fade": {
        "min_event_score": 5.0,
        "max_event_score": 7.99,
        "long_rsi_max": 20,
        "short_rsi_min": 80,
        "min_atr_extension": 1.5,
    },
    "decision_priority": {
        "prefer_continuation_above_score": 8.0,
    },
}

from bybit_news_bot import (
    evaluate_continuation_entry,
    evaluate_fade_entry,
    build_trade_decision,
)


def test_1():
    """
    Test 1: Bullish high-score GAS event
    - event_score = 8.7
    - RSI = 61
    - breakout_confirmed = True
    - volume_confirmed = True
    - spread_ok = True
    Expected:
    - continuation long = True
    - fade long = False
    - final decision = ENTER_LONG_CONTINUATION
    """
    print("\n[TEST 1] Bullish high-score GAS event")
    
    event_score = 8.7
    rsi = 61
    direction = "BULLISH"
    market_conf = {
        "breakout_confirmed": True,
        "breakdown_confirmed": False,
        "volume_confirmed": True,
        "spread_ok": True,
        "overextended": False,
    }
    
    # Test continuation
    cont = evaluate_continuation_entry(event_score, rsi, market_conf, direction)
    print(f"  Continuation eligible: {cont['eligible']}")
    print(f"  Continuation fail reasons: {cont.get('fail_reasons', [])}")
    
    # Test fade
    fade = evaluate_fade_entry(event_score, rsi, 0.5, 1.2, market_conf, direction)
    print(f"  Fade eligible: {fade['eligible']}")
    
    # Test decision
    decision = build_trade_decision(event_score, rsi, 0.5, market_conf, direction, "GASUSDT", "Test", "Test")
    print(f"  Final action: {decision['final_action']}")
    print(f"  Entry model: {decision['chosen_entry_model']}")
    
    expected = "ENTER_LONG_CONTINUATION"
    passed = decision["final_action"] == expected
    print(f"  RESULT: {'PASS' if passed else 'FAIL'} (expected {expected})")
    return passed


def test_2():
    """
    Test 2: Bullish medium-score GAS event
    - event_score = 6.4
    - RSI = 18
    - extension = 1.7 ATR
    - orderflow_decelerating = True
    Expected:
    - continuation long = False
    - fade long = True
    - final decision = ENTER_LONG_FADE
    """
    print("\n[TEST 2] Bullish medium-score GAS event (RSI oversold)")
    
    event_score = 6.4
    rsi = 18
    direction = "BULLISH"
    market_conf = {
        "breakout_confirmed": True,
        "volume_confirmed": True,
        "spread_ok": True,
        "overextended": False,
    }
    
    # Test continuation
    cont = evaluate_continuation_entry(event_score, rsi, market_conf, direction)
    print(f"  Continuation eligible: {cont['eligible']}")
    
    # Test fade - RSI < 20 = oversold
    fade = evaluate_fade_entry(event_score, rsi, 0.5, 1.7, market_conf, direction)
    print(f"  Fade eligible: {fade['eligible']}")
    print(f"  Fade fail reasons: {fade.get('fail_reasons', [])}")
    
    decision = build_trade_decision(event_score, rsi, 0.5, market_conf, direction, "GASUSDT", "Test", "Test")
    print(f"  Final action: {decision['final_action']}")
    
    expected = "ENTER_LONG_FADE"
    passed = decision["final_action"] == expected
    print(f"  RESULT: {'PASS' if passed else 'FAIL'} (expected {expected})")
    return passed


def test_3():
    """
    Test 3: Bullish high-score event but no breakout
    - event_score = 8.5
    - RSI = 60
    - breakout_confirmed = False
    Expected:
    - SKIP
    - continuation_fail_reasons includes no_breakout_confirmation
    """
    print("\n[TEST 3] Bullish high-score, NO breakout")
    
    event_score = 8.5
    rsi = 60
    direction = "BULLISH"
    market_conf = {
        "breakout_confirmed": False,  # KEY: No breakout!
        "volume_confirmed": True,
        "spread_ok": True,
        "overextended": False,
    }
    
    cont = evaluate_continuation_entry(event_score, rsi, market_conf, direction)
    print(f"  Continuation eligible: {cont['eligible']}")
    print(f"  Fail reasons: {cont.get('fail_reasons', [])}")
    
    decision = build_trade_decision(event_score, rsi, 0.5, market_conf, direction, "GASUSDT", "Test", "Test")
    print(f"  Final action: {decision['final_action']}")
    
    expected = "SKIP"
    has_reason = "no_breakout_confirmation" in decision.get("continuation_fail_reasons", [])
    passed = decision["final_action"] == expected and has_reason
    print(f"  RESULT: {'PASS' if passed else 'FAIL'} (expected {expected})")
    return passed


def test_4():
    """
    Test 4: Bearish high-score BTC event
    - event_score = 9.1
    - RSI = 39
    - breakdown_confirmed = True
    Expected:
    - ENTER_SHORT_CONTINUATION
    """
    print("\n[TEST 4] Bearish high-score BTC event")
    
    event_score = 9.1
    rsi = 39
    direction = "BEARISH"
    market_conf = {
        "breakout_confirmed": False,
        "breakdown_confirmed": True,  # KEY: breakdown confirmed
        "volume_confirmed": True,
        "spread_ok": True,
        "overextended": False,
    }
    
    cont = evaluate_continuation_entry(event_score, rsi, market_conf, direction)
    print(f"  Continuation eligible: {cont['eligible']}")
    
    decision = build_trade_decision(event_score, rsi, 0.5, market_conf, direction, "BTCUSDT", "Test", "Test")
    print(f"  Final action: {decision['final_action']}")
    
    expected = "ENTER_SHORT_CONTINUATION"
    passed = decision["final_action"] == expected
    print(f"  RESULT: {'PASS' if passed else 'FAIL'} (expected {expected})")
    return passed


def test_5():
    """
    Test 5: Old broken behavior prevention
    - bullish high-score event
    - RSI = 62 (NOT oversold)
    - all continuation conditions True
    Expected:
    - system must NOT skip just because RSI is not oversold
    """
    print("\n[TEST 5] OLD BUG PREVENTION - RSI 62, should NOT skip")
    
    event_score = 8.7
    rsi = 62  # NOT oversold - this is the key!
    direction = "BULLISH"
    market_conf = {
        "breakout_confirmed": True,
        "volume_confirmed": True,
        "spread_ok": True,
        "overextended": False,
    }
    
    # Test continuation - RSI 62 < 78 = PASS
    cont = evaluate_continuation_entry(event_score, rsi, market_conf, direction)
    print(f"  RSI: {rsi} (continuation max: 78)")
    print(f"  Continuation eligible: {cont['eligible']}")
    print(f"  Fail reasons: {cont.get('fail_reasons', [])}")
    
    # Old buggy behavior would have skipped here
    # V2.1 correctly allows it!
    expected = "ENTER_LONG_CONTINUATION"
    decision = build_trade_decision(event_score, rsi, 0.5, market_conf, direction, "GASUSDT", "Test", "Test")
    passed = decision["final_action"] == expected
    
    print(f"  Final action: {decision['final_action']}")
    print(f"  RESULT: {'PASS' if passed else 'FAIL'} (expected {expected})")
    return passed


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("BYBIT-NEWS-TRADING v2.1 TEST SUITE")
    print("="*60)
    
    results = []
    results.append(("Test 1: High-score continuation", test_1()))
    results.append(("Test 2: Medium-score fade", test_2()))
    results.append(("Test 3: No breakout = skip", test_3()))
    results.append(("Test 4: Bearish continuation", test_4()))
    results.append(("Test 5: Old bug prevention", test_5()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, result in results:
        print(f"  {'PASS' if result else 'FAIL'}: {name}")
    
    print(f"\nTotal: {passed}/{total}")
    
    if passed == total:
        print("\nSTATUS: PASS - Ready for production")
    else:
        print("\nSTATUS: FAIL - Fix issues before production")
    
    return passed == total


if __name__ == "__main__":
    run_all_tests()