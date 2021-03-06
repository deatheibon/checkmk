#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import logging
import socket

import pytest  # type: ignore[import]

from cmk.base.check_utils import ServiceCheckResult
from cmk.base.data_sources.tcp import TCPDataFetcher, TCPDataSource
import cmk.base.data_sources.abstract as _abstract
from cmk.base.exceptions import MKAgentError
from testlib.base import Scenario


@pytest.mark.parametrize("result,reported,rule", [
    (None, "127.0.0.1", None),
    (None, None, "127.0.0.1"),
    ((0, 'Allowed IP ranges: 1.2.3.4', []), "1.2.3.4", "1.2.3.4"),
    ((1, 'Unexpected allowed IP ranges (exceeding: 1.2.4.6 1.2.5.6)(!)', []), "1.2.{3,4,5}.6",
     "1.2.3.6"),
    ((1, 'Unexpected allowed IP ranges (missing: 1.2.3.4 1.2.3.5)(!)', []), "1.2.3.6",
     "1.2.3.{4,5,6}"),
])
def test_tcpdatasource_only_from(monkeypatch, result, reported, rule):
    ts = Scenario().add_host("hostname")
    ts.set_option("agent_config", {"only_from": [rule]} if rule else {})
    config_cache = ts.apply(monkeypatch)

    source = TCPDataSource("hostname", "ipaddress")
    monkeypatch.setattr(config_cache, "host_extra_conf", lambda host, ruleset: ruleset)
    assert source._sub_result_only_from({"onlyfrom": reported}) == result


@pytest.mark.parametrize("ipaddress", [None, "127.0.0.1"])
def test_attribute_defaults(monkeypatch, ipaddress):
    hostname = "testhost"
    Scenario().add_host(hostname).apply(monkeypatch)
    source = TCPDataSource(hostname, ipaddress)

    assert source._hostname == hostname
    assert source._ipaddress == ipaddress
    assert source.id() == "agent"
    assert source.port == 6556
    assert source.timeout == 5.0
    # From the base class
    assert source.get_check_plugin_names() == set()
    assert source.name() == ("agent:%s:%s" % (hostname, ipaddress if ipaddress else ""))
    assert source.describe() == "TCP: %s:%s" % (ipaddress, source.port)
    assert source.is_agent_cache_disabled() is False
    assert source.get_may_use_cache_file() is False
    assert source.exception() is None


@pytest.mark.parametrize("ipaddress", [None, "127.0.0.1"])
def test_get_summary_result_requires_host_sections(monkeypatch, ipaddress):
    hostname = "testhost"
    Scenario().add_host(hostname).apply(monkeypatch)
    source = TCPDataSource(hostname, ipaddress)

    with pytest.raises(AssertionError):
        source.get_summary_result_for_discovery()
    with pytest.raises(AssertionError):
        source.get_summary_result_for_inventory()
    with pytest.raises(AssertionError):
        source.get_summary_result_for_checking()

    source._host_sections = _abstract.AgentHostSections()

    defaults = (0, "Version: unknown, OS: unknown", [])  # type: ServiceCheckResult
    assert source.get_summary_result_for_discovery() == defaults
    assert source.get_summary_result_for_inventory() == defaults
    assert source.get_summary_result_for_checking() == defaults


def test_decrypt_plaintext_is_noop():
    settings = {"use_regular": "allow"}
    output = b"<<<section:sep(0)>>>\nbody\n"
    fetcher = TCPDataFetcher(socket.AF_INET, "127.0.0.1", 0.0, settings, logging.getLogger("test"))

    assert fetcher._decrypt(output) == output


def test_decrypt_plaintext_with_enforce_raises_MKAgentError():
    settings = {"use_regular": "enforce"}
    output = b"<<<section:sep(0)>>>\nbody\n"
    fetcher = TCPDataFetcher(socket.AF_INET, "127.0.0.1", 0.0, settings, logging.getLogger("test"))

    with pytest.raises(MKAgentError):
        fetcher._decrypt(output)


def test_decrypt_payload_with_wrong_protocol_raises_MKAgentError():
    settings = {"use_regular": "enforce"}
    output = b"the first two bytes are not a number"
    fetcher = TCPDataFetcher(socket.AF_INET, "127.0.0.1", 0.0, settings, logging.getLogger("test"))

    with pytest.raises(MKAgentError):
        fetcher._decrypt(output)
