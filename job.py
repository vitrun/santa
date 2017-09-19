#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import argparse

from santa import Santa


if __name__ == '__main__':
    arger = argparse.ArgumentParser(__file__)
    arger.add_argument('job', type=str)

    args = arger.parse_args()
    if args.job == 'refund':
        Santa.refund_job()
    elif args.job == 'claim':
        Santa.claim_job()
    else:
        print('Invalid job')
