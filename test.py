#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

from santa import Santa, SimpleException


def test_claim_all():
    num, total = 5, 301
    envelope = Santa.create_envelope(1, total, num)
    cents = []
    for i in range(num):
        doc = Santa.claim_envelope(i, envelope.id, envelope.secret)
        cents.append(doc['cent'])
    assert sum(cents) == total


def test_claim_twice():
    envelope = Santa.create_envelope(1, 300, 3)
    Santa.claim_envelope(1, envelope.id, envelope.secret)
    try:
        Santa.claim_envelope(1, envelope.id, envelope.secret)
    except Exception as e:
        assert type(e) == SimpleException


def test_insufficient():
    num = 5
    envelope = Santa.create_envelope(1, 300, num)
    for i in range(num):
        Santa.claim_envelope(i, envelope.id, envelope.secret)
    try:
        Santa.claim_envelope(num, envelope.id, envelope.secret)
    except Exception as e:
        assert type(e) == SimpleException


if __name__ == '__main__':
    # test_claim_all()
    test_claim_twice()
    # test_insufficient()
