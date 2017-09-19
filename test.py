#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

from santa import Santa, SimpleException


def test_claim_all():
    """
    多个红包领完后钱应能对上
    """
    _claim_all(5)


def test_claim_one():
    """
    单个红包领完后钱应能对上
    """
    _claim_all(1)


def _claim_all(num):
    total = 301
    envelope = Santa.create_envelope(1, total, num)
    cents = []
    for i in range(num):
        claim = Santa.claim_envelope(i, envelope.id, envelope.secret)
        cents.append(claim.cent)
    assert sum(cents) == total


def test_claim_twice():
    """
    试图领两个应拋错
    """
    envelope = Santa.create_envelope(1, 300, 3)
    Santa.claim_envelope(1, envelope.id, envelope.secret)
    try:
        Santa.claim_envelope(1, envelope.id, envelope.secret)
    except Exception as e:
        assert type(e) == SimpleException


def test_insufficient():
    """
    领光了应拋错
    """
    num = 5
    envelope = Santa.create_envelope(1, 300, num)
    for i in range(num):
        Santa.claim_envelope(i, envelope.id, envelope.secret)
    try:
        Santa.claim_envelope(num, envelope.id, envelope.secret)
    except Exception as e:
        assert type(e) == SimpleException


def test_gen_secret():
    """
    红包口令
    """
    assert len(Santa.gen_secret(1)) == 1
    assert len(Santa.gen_secret(99)) == 99


if __name__ == '__main__':
    test_claim_all()
    test_claim_twice()
    test_insufficient()
