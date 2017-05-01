#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2017 Chintalagiri Shashank
# Released under the MIT license.

"""
Worker for a vendor data maintenance server using Twisted for Tendril
"""

import json
import pika
from pika.adapters import twisted_connection
from twisted.internet import defer, reactor, protocol, task
from twisted.python import log

from tendril.sourcing import electronics
from tendril.sourcing.db import controller
from tendril.utils.db import get_session
from tendril.sourcing.vendors.vendorbase import VendorPartRetrievalError

from tendril.utils.config import MQ_SERVER
from tendril.utils.config import MQ_SERVER_PORT

import logging
logging.basicConfig(level=logging.INFO)


@defer.inlineCallbacks
def monitor_vpinfo(connection):
    channel = yield connection.channel()
    yield channel.queue_declare(
        queue='maintenance_vendor_vpinfo',
        durable=True, auto_delete=False, exclusive=False
    )
    queue_object_vpmap, consumer_tag = yield channel.basic_consume(
        queue='maintenance_vendor_vpinfo', no_ack=False
    )
    l = task.LoopingCall(process_vpinfo, queue_object_vpmap, connection)
    l.start(0.01)


@defer.inlineCallbacks
def monitor_vpmap(connection):
    channel = yield connection.channel()
    yield channel.queue_declare(
        queue='maintenance_vendor_vpmap',
        durable=True, auto_delete=False, exclusive=False
    )
    queue_object_vpinfo, consumer_tag = yield channel.basic_consume(
        queue='maintenance_vendor_vpmap', no_ack=False
    )
    l = task.LoopingCall(process_vpmap, queue_object_vpinfo, connection)
    l.start(0.01)


@defer.inlineCallbacks
def process_vpinfo(queue_object, connection):
    ch, method, properties, body = yield queue_object.get()
    if body:
        request = json.loads(body)
        ident = request['ident']
        vendor = electronics.get_vendor_by_name(request['vendor'])
        try:
            vendor.get_vpart(request['vpno'], ident, 0)
            print("Got fresh part for {0} {1}".format(vendor, request['vpno']))
        except VendorPartRetrievalError:
            log.msg(
                "Permanent Retrieval Error while getting part {0} from {1}. "
                "Remove from Map? ".format(request['vpno'], vendor.name)
            )
            # TODO Make sure this is safe before turning this on!
            # vendor.map.remove_apartno(request['vpno'], ident)
            raise
        except:
            log.msg("Unhandled Error while getting part {0} from {1}"
                    "".format(request['vpno'], vendor.name))
            raise
    yield ch.basic_ack(delivery_tag=method.delivery_tag)


@defer.inlineCallbacks
def process_vpmap(queue_object, connection):
    ch, method, properties, body = yield queue_object.get()
    if body:
        print body
        request = json.loads(body)
        ident = request['ident']
        vendor = electronics.get_vendor_by_name(request['vendor'])
        vendor_obj = controller.get_vendor(name=vendor.cname)
        vpnos, strategy = vendor.search_vpnos(ident)
        if vpnos is not None:
            avpnos = vpnos
        else:
            if strategy not in ['NODEVICE', 'NOVALUE',
                                'NOT_IMPL']:
                log.msg("Not Found: {0:40}::{1}\n".format(ident, strategy))
            avpnos = []
        with get_session() as session:
            print("Update Map {0:12}:{1:40}::{2:28}"
                  "".format(vendor.cname, ident, avpnos))
            log.msg("VMAP {0:12}:{1:40}::{2:28}"
                    "".format(vendor.cname, ident, avpnos))
            controller.set_strategy(vendor=vendor_obj, ident=ident,
                                    strategy=strategy, session=session)
            controller.set_amap_vpnos(vendor=vendor_obj, ident=ident,
                                      vpnos=avpnos, session=session)
    yield ch.basic_ack(delivery_tag=method.delivery_tag)


def start():
    parameters = pika.ConnectionParameters()

    log.msg('Starting vendor maintenance queue monitors')

    cc0 = protocol.ClientCreator(
        reactor, twisted_connection.TwistedProtocolConnection, parameters
    )
    d0 = cc0.connectTCP(MQ_SERVER, MQ_SERVER_PORT)
    d0.addCallback(lambda x: x.ready)
    d0.addCallback(monitor_vpinfo)

    cc1 = protocol.ClientCreator(
        reactor, twisted_connection.TwistedProtocolConnection, parameters
    )
    d1 = cc1.connectTCP(MQ_SERVER, MQ_SERVER_PORT)
    d1.addCallback(lambda x: x.ready)
    d1.addCallback(monitor_vpmap)
