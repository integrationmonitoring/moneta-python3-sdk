#!/usr/bin/env python3

from configparser import ConfigParser

# import templates
from monetasdktemplates import *

import suds
from suds.client import Client
from suds.wsse import *

# md5 lib
import hashlib

# show debug info
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)

# read config files
import os
additional_config = ConfigParser()
additional_config.read('config/additional_field_names.ini')
basic_config = ConfigParser()
basic_config.read('config/basic_settings.ini')
error_texts_config = ConfigParser()
error_texts_config.read('config/error_texts.ini')
payment_systems_config = ConfigParser()
payment_systems_config.read('config/payment_systems.ini')
payment_urls_config = ConfigParser()
payment_urls_config.read('config/payment_urls.ini')
success_config = ConfigParser()
success_config.read('config/success_fail_urls.ini')

# use settings and set evironment
mnt_login = basic_config.get('basic', 'monetasdk_account_username').strip(' \t\n\r')
mnt_pwd = basic_config.get('basic', 'monetasdk_account_password').strip(' \t\n\r')

wsdlChunks = []
if basic_config.get('basic', 'monetasdk_demo_mode').strip(' \t\n\r') == '1':
    wsdlChunks.append(payment_urls_config.get('payment_urls', 'monetasdk_demo_url').strip(' \t\n\r'))
else:
    wsdlChunks.append(payment_urls_config.get('payment_urls', 'monetasdk_production_url').strip(' \t\n\r'))
  
wsdlChunks.append(payment_urls_config.get('payment_urls', 'monetasdk_soap_link').strip(' \t\n\r'))  
wsdl = ''.join(wsdlChunks)

# connect to wsdl
client = Client(wsdl, cache=None)
security = Security()
token = UsernameToken(mnt_login, mnt_pwd)
security.tokens.append(token)   
client.set_options(wsse=security, port='MessagesSoap11')


# SDK functions:


def showChoosePaymentSystemForm():
    response = bool(0)
    error = bool(0)
    render = templateChoosePaymentSystemForm('choosepaymentsystem')
    return {"data": response, "render": render, "error": error}


def showPaymentFrom(orderId, amount, currency='RUB', description='', paysys=''):
    response = bool(0)
    error = bool(0)
    render = templatePaymentFrom(paysys, 'generatepaymentform', orderId, amount, currency, description)
    return {"data": response, "render": render, "error": error}


def showAccountBalance(accountId=0):
    response = bool(0)
    render = bool(0)
    error = bool(0)
    try:
        response = client.service.FindAccountsList()
        if response:
            while response:
                node = response.pop()
                if accountId == 0 or node.id == accountId:
                    render = templateAccountBalance(node.id, node.balance, node.availableBalance, node.currency)
                    break

    except suds.WebFault as e:
        error = e
    return {"data": response, "render": render, "error": error}


def showOperationInfo(operationId):
    response = bool(0)
    render = bool(0)
    error = bool(0)
    try:
        response = client.service.GetOperationDetailsById(operationId)
    except suds.WebFault as e:
        error = e
    if response:
        render = templateOperationInfo(response)
    else:
        render = bool(0)
    return {"data": response, "render": render, "error": error}


def processInputData(MNT_ID, MNT_TRANSACTION_ID, MNT_OPERATION_ID, MNT_AMOUNT, MNT_CURRENCY_CODE, MNT_SUBSCRIBER_ID, MNT_TEST_MODE, MNT_SIGNATURE):
    response = bool(0)
    render = 'FAIL'
    error = bool(0)
    basic_config = ConfigParser()
    basic_config.read('config/basic_settings.ini')
    accountCode = basic_config.get('basic', 'monetasdk_account_code')
    signatureChunks = list()
    signatureChunks.append(MNT_ID.strip(' \t\n\r'))
    signatureChunks.append(MNT_TRANSACTION_ID.strip(' \t\n\r'))
    signatureChunks.append(MNT_OPERATION_ID.strip(' \t\n\r'))
    signatureChunks.append(MNT_AMOUNT.strip(' \t\n\r'))
    signatureChunks.append(MNT_CURRENCY_CODE.strip(' \t\n\r'))
    signatureChunks.append(MNT_SUBSCRIBER_ID.strip(' \t\n\r'))
    signatureChunks.append(MNT_TEST_MODE.strip(' \t\n\r'))
    signatureChunks.append(accountCode.strip(' \t\n\r'))
    signature = ''.join(signatureChunks)
    signatureMd5 = hashlib.md5(signature.encode('utf-8')).hexdigest()
    if accountCode and signatureMd5 != MNT_SIGNATURE:
        render = 'FAIL'
    else:
        render = 'SUCCESS'
    return {"data": response, "render": render, "error": error}


def sdkGetProfileInfo(setUnitId):
    error = bool(0)
    response = bool(0)
    try:
        response = client.service.GetProfileInfo(unitId=setUnitId)
    except suds.WebFault as e:
        error = e
    if response:
        render = templateProfileInfo(response)
    else:
        render = bool(0)
    return {"data": response, "render": render, "error": error}


def getAdditionalFieldsByPaymentSystem(paymentSystem='payanyway'):
    result = []
    if paymentSystem == 'post':
        result = ['additionalParameters_mailofrussiaSenderIndex',
                  'additionalParameters_mailofrussiaSenderRegion',
                  'additionalParameters_mailofrussiaSenderAddress',
                  'additionalParameters_mailofrussiaSenderName']
    if paymentSystem == 'euroset':
        result = ['additionalParameters_rapidaPhone']
    if paymentSystem == 'qiwi':
        result = ['additionalParameters_qiwiUser']
    return result


def getValueFromArray(value, array):
    if not array[value]:
        raise Exception('No value in array')
    return array[value]


def checkParamsInArray(inputData, params):
    result = True
    if not len(params):
        result = False
    for param in params:
        if not getValueFromArray(param,inputData):
            result = False
    return result


def checkAdditionalData(paymentSystem='payanyway', additionalData=None):
    result = True
    if paymentSystem == 'post':
        result = checkParamsInArray(additionalData, getAdditionalFieldsByPaymentSystem(paymentSystem))
    if paymentSystem == 'euroset':
        result = checkParamsInArray(additionalData, getAdditionalFieldsByPaymentSystem(paymentSystem))
    return result


def createInvoice(payer, payee, amount, orderId, paymentSystem='payanyway', isRegular=False, additionalData=None):
    response = bool(False)
    error = None
    try:
        operationInfo = dict()
        operationInfo['attribute'] = list()
        if isRegular:
            operationInfo['attribute']['PAYMENTTOKEN'] = 'request'
        if paymentSystem == 'post' and additionalData and checkAdditionalData(paymentSystem, additionalData):
            if additionalData['additionalParameters_mailofrussiaSenderIndex']:
                operationInfo['attribute']['mailofrussiaindex'] = \
                    additionalData['additionalParameters_mailofrussiaSenderIndex']
            if additionalData['additionalParameters_mailofrussiaSenderRegion']:
                operationInfo['attribute']['mailofrussiaregion'] = \
                    additionalData['additionalParameters_mailofrussiaSenderRegion']
            if additionalData['additionalParameters_mailofrussiaSenderAddress']:
                operationInfo['attribute']['mailofrussiaaddress'] = \
                    additionalData['additionalParameters_mailofrussiaSenderAddress']
            if additionalData['additionalParameters_mailofrussiaSenderName']:
                operationInfo['attribute']['mailofrussianame'] = \
                    additionalData['additionalParameters_mailofrussiaSenderName']
        elif paymentSystem == 'euroset' and additionalData and checkAdditionalData(paymentSystem, additionalData):
            if additionalData['additionalParameters_rapidaPhone']:
                operationInfo['attribute']['rapidamphone'] = additionalData['additionalParameters_rapidaPhone']
        elif paymentSystem == 'qiwi' and additionalData and checkAdditionalData(paymentSystem, additionalData):
            if additionalData['additionalParameters_qiwiUser']:
                operationInfo['attribute']['QIWIPHONE'] = additionalData['additionalParameters_qiwiUser']
            if additionalData['additionalParameters_qiwiComment']:
                operationInfo['attribute']['qiwicomment'] = additionalData['additionalParameters_qiwiComment']
            if additionalData['additionalParameters_ownerLogin']:
                operationInfo['attribute']['ownerlogin'] = additionalData['additionalParameters_ownerLogin']
        try:
            additionalData['AUTHORIZEONLY']
        except TypeError:
            pass
        else:
            operationInfo['attribute']['AUTHORIZEONLY'] = additionalData['AUTHORIZEONLY']
        response = client.service.Invoice(payer=payer,
                                          payee=payee,
                                          amount=amount,
                                          clientTransaction=orderId,
                                          operationInfo=operationInfo)
    except suds.WebFault as e:
        error = e
    return {"data": response, "render": None, "error": error}
