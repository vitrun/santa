#! /usr/bin/env python
# -*- coding: utf-8 -*-

import redis
import random
import logging
import json
import string

from json import JSONDecodeError
from dao import Envelope, Claim, Wallet

logging.basicConfig(level=logging.DEBUG)

client = redis.StrictRedis(host='localhost', port=6379, db=0)
request_timeout = 3.0


class SimpleException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


class Santa:
    @staticmethod
    def gen_secret():
        """
        生成口令
        """
        literal = '123456789' + ''.join([x for x in string.ascii_letters if x not in ('l', 'O')])
        chars = [random.choice(literal) for _ in range(8)]
        return ''.join(chars)

    @staticmethod
    def create_envelope(user_id, cent, num):
        """
        发红包
        """
        secret = Santa.gen_secret()
        envelope = Envelope(user_id=user_id, total_cent=cent, total_num=num,
                            remain_num=num, remain_cent=cent, secret=secret)
        envelope.save(client)
        return envelope

    @staticmethod
    def claim_envelope(user_id, env_id, secret):
        """
        领红包
        """
        #: has ever claimed?
        if Envelope.has_claimed(client, user_id, env_id):
            raise SimpleException('Already claimed.')

        #: check secret
        if secret.encode('utf8') != Envelope.get(client, env_id).secret:
            raise SimpleException('Invalid secret')

        if not Envelope.claim(client, env_id):
            raise SimpleException('No more envelopes.')

        claim = Claim(user_id=user_id, envelope_id=env_id, cent=0)
        #: save the claim to db
        claim.save(client)

        #: publish the claim
        Santa.publish(client, claim)

        #: subscribe to the result
        sub = client.pubsub()
        channel = Santa.subscribe(claim, sub)
        #: ignore the subscription message
        _ = sub.get_message(timeout=request_timeout)
        res = sub.get_message(timeout=request_timeout)
        try:
            return json.loads(res['data'])
        except (JSONDecodeError, TypeError):
            raise SimpleException("failed to get result")
        finally:
            sub.unsubscribe(channel)

    @staticmethod
    def publish(cli, claim):
        claim_channel = 'envelope:claim:queue'
        logging.debug("pubishing to %s: %s", claim_channel, claim.dic)
        cli.publish(claim_channel, json.dumps(claim.dic))

    @staticmethod
    def subscribe(claim, sub):
        result_channel = 'envelope:claim:result:%d' % claim.id
        sub.subscribe(result_channel)
        logging.debug('subscribing from %s', result_channel)
        #: mark the claim
        Envelope.mark_claimed(client, claim.user_id, claim.envelope_id)
        return result_channel

    @staticmethod
    def do_claim(claim):
        """
        领纸包实际逻辑
        """
        envelope = Envelope.get(client, claim.envelope_id)

        remain_cent = int(envelope.remain_cent)
        remain_num = int(envelope.remain_num)
        assert remain_cent > remain_num
        #: decide the amount, ensure at least 1 cent for others
        claim.cent = remain_cent if remain_num <= 0 else \
            random.randrange(1, remain_cent - remain_num)
        logging.debug("remain cent: %d, remain num:%d", remain_cent, remain_num)

        #: update the envelope and the wallet
        envelope.decr_cent(client, claim.cent)
        Wallet.incr(client, claim.user_id, claim.cent)
        claim.record(client)

        #: publish the claim result
        result_channel = 'envelope:claim:result:%s' % claim.id
        logging.debug('publishing to %s: %s', result_channel, claim.dic)
        client.publish(result_channel, json.dumps(claim.dic))

    @staticmethod
    def refund_job():
        """
        红包过期退款
        """
        #: 逐出或过期时通知
        client.config_set('config set notify-keyspace-events', 'Kxe')
        sub = client.pubsub()
        sub.psubscribe('__keyspace*__:envelope:expire:*')
        for msg in sub.listen():
            if msg['type'] == 'subscribe':
                continue
            envelope_id = msg['key'].split(':')[-1]
            envelope = client.hgetall('envelope:%d' % envelope_id)
            if int(envelope.get('remain_num')) <= 0:
                continue
            #: 退到余额
            user_id, remain_cent = envelope['uid'], envelope['remain_cent']
            logging.debug("refunding %s to user %s", remain_cent, user_id)
            Wallet.incr(client, user_id, remain_cent)

    @staticmethod
    def claim_job():
        """
        领红包任务队列
        """
        #: TODO. scale out by using multiple queues
        claim_channel = 'envelope:claim:queue'
        sub = client.pubsub()
        sub.subscribe(claim_channel)
        for msg in sub.listen():
            try:
                if msg['type'] == 'subscribe':
                    continue
                claim_dic = json.loads(msg['data'])
                claim = Claim(**claim_dic)
                Santa.do_claim(claim)
            except (JSONDecodeError, TypeError):
                logging.error("failed to consume %s", msg)
