#!/usr/bin/env python

import hashlib
import ConfigParser, os

# template classes
class Node(object):
    def __init__(self, params, children):
        self.params = params
        self.children = children


class IfNode(Node):
    def render(self, context):
        test = eval(self.params['test'], globals(), context)
        if test:
            yield iter(self.children)


class ForNode(Node):
    def render(self, context):
        src = eval(self.params['src'], globals(), context)
        dst = self.params['dst']
        for obj in src:
            context[dst] = obj
            yield iter(self.children)

# template render method            
def render(template, **context):
    output = []
    stack = [iter(template)]

    while stack:
        node = stack.pop()
        if isinstance(node, basestring):
            output.append(node.format(**context))
        elif isinstance(node, Node):
            stack.append(node.render(context))
        else:
            new_node = next(node, None)
            if new_node is not None:
                stack.append(node)
                stack.append(new_node)
    return "".join(output)


def templateChoosePaymentSystemForm(formName='mntchoosepaysys'):

    payment_systems_config = ConfigParser.RawConfigParser()
    payment_systems_config.read('config/payment_systems.ini')

    template = [
    "<h1>Choose payment way:</h1>",
    "<form name={formName} method=get>",
        "<input type=radio name=paysys value='{pv1}' selected='selected' /> {pn1}",
        "<input type=radio name=paysys value='{pv2}' /> {pn2}",
        "<input type=radio name=paysys value='{pv3}' /> {pn3}",
        "<input type=radio name=paysys value='{pv4}' /> {pn4}",
        "<input type=radio name=paysys value='{pv5}' /> {pn5}",
        "<input type=radio name=paysys value='{pv6}' /> {pn6}",
        "<input type=radio name=paysys value='{pv7}' /> {pn7}",
        "<input type=radio name=paysys value='{pv8}' /> {pn8}",
        "<input type=submit value='Choose' />",
    "</form>"
    ]

    return(render(template, formName = formName, pv1 = 'payanyway', pn1 = payment_systems_config.get('monetasdk_paysys_payanyway', 'title'),
        pv2 = 'moneta', pn2 = payment_systems_config.get('monetasdk_paysys_moneta', 'title'),
        pv3 = 'walletone', pn3 = payment_systems_config.get('monetasdk_paysys_walletone', 'title'),
        pv4 = 'yandex', pn4 = payment_systems_config.get('monetasdk_paysys_yandex', 'title'),
        pv5 = 'qiwi', pn5 = payment_systems_config.get('monetasdk_paysys_qiwi', 'title'),
        pv6 = 'euroset', pn6 = payment_systems_config.get('monetasdk_paysys_euroset', 'title'),
        pv7 = 'sberbank', pn7 = payment_systems_config.get('monetasdk_paysys_sberbank', 'title'),
        pv8 = 'plastic', pn8 = payment_systems_config.get('monetasdk_paysys_plastic', 'title') ))


def templatePaymentFrom(paysys, formName, orderId, amount, currency, description=''):

    if (formName == ''):
       formName = 'mntpay'

    if (currency == ''):
       currency = 'RUB'

    amount = "%.2f" % round(amount, 2)

    basic_config = ConfigParser.RawConfigParser()
    basic_config.read('config/basic_settings.ini')
    payment_systems_config = ConfigParser.RawConfigParser()
    payment_systems_config.read('config/payment_systems.ini')
    payment_urls_config = ConfigParser.RawConfigParser()
    payment_urls_config.read('config/payment_urls.ini')
    success_config = ConfigParser.RawConfigParser()
    success_config.read('config/success_fail_urls.ini')

    urlChunks = []
    if (basic_config.get('basic', 'monetasdk_demo_mode').strip(' \t\n\r') == '1'):
        urlChunks.append(payment_urls_config.get('payment_urls', 'monetasdk_demo_url').strip(' \t\n\r'))
    else:
        urlChunks.append(payment_urls_config.get('payment_urls', 'monetasdk_production_url').strip(' \t\n\r'))

    urlChunks.append(payment_urls_config.get('payment_urls', 'monetasdk_assistant_link').strip(' \t\n\r'))  
    formAction = ''.join(urlChunks)

    accountId = basic_config.get('basic', 'monetasdk_account_id')
    accountCode = basic_config.get('basic', 'monetasdk_account_code')
    testMode = basic_config.get('basic', 'monetasdk_demo_mode')
    successUrl = success_config.get('success', 'monetasdk_success_url')
    failUrl = success_config.get('success', 'monetasdk_fail_url')

    signatureChunks = []
    signatureChunks.append(accountId.strip(' \t\n\r'))
    signatureChunks.append(orderId)
    signatureChunks.append(amount.strip(' \t\n\r'))
    signatureChunks.append(currency.strip(' \t\n\r'))
    signatureChunks.append(testMode.strip(' \t\n\r'))
    signatureChunks.append(accountCode.strip(' \t\n\r'))
    signature = ''.join(signatureChunks)
    signatureMd5 = hashlib.md5(signature.encode('utf-8')).hexdigest()

    template = [
    "<h1>Click pay button</h1>",
    "<form name={formName} method=get action={formAction}>",
        "<input type=hidden name=MNT_ID value='{accountId}' />",
        "<input type=hidden name=MNT_TRANSACTION_ID value='{orderId}' />",
        "<input type=hidden name=MNT_AMOUNT value='{amount}' />",
        "<input type=hidden name=MNT_CURRENCY_CODE value='{currency}' />",
        "<input type=hidden name=MNT_TEST_MODE value='{testMode}' />"
    ]

    unitId = ''
    if (paysys and paysys != ''):
        paysysChunks = []
        paysysChunks.append('monetasdk_paysys_')
        paysysChunks.append(paysys)
        paysysGroup = ''.join(paysysChunks)
        unitId = payment_systems_config.get(paysysGroup, 'unitId')
        template.append("<input type=hidden name=paymentSystem.unitId value='{unitId}' />")
        template.append("<input type=hidden name=paymentSystem.limitIds value='{unitId}' />")

    if (successUrl and successUrl != ''):   
        template.append("<input type=hidden name=MNT_SUCCESS_URL value='{successUrl}' />")

    if (failUrl and failUrl != ''):
        template.append("<input type=hidden name=MNT_FAIL_URL value='{failUrl}' />")

    if (description and description != ''):
        template.append("<input type=hidden name=MNT_DESCRIPTION value='{description}' />")

    if (accountCode and accountCode != ''):
        template.append("<input type=hidden name=MNT_SIGNATURE value='{signatureMd5}' />")

    template.append("<input type=submit value='Pay' />")
    template.append("</form>")

    return(render(template, formName = formName, formAction = formAction, accountId = accountId, orderId = orderId,
                  amount = amount, currency = currency, testMode = testMode, unitId = unitId, successUrl = successUrl,
                  failUrl = failUrl, description = description, signatureMd5 = signatureMd5))


def templateAccountBalance(accountId, balance, availableBalance, currency):
    template = [
    "<h1>Account info:</h1>",
    "<ul>",
        "<li><b>Account ID:</b> {accountId}</li>",
        "<li><b>Balance:</b> {balance}</li>",
        "<li><b>Available balance:</b> {availableBalance}</li>",
        "<li><b>Currency:</b> {currency}</li>",
    "</ul>"
    ]
    
    return(render(template, accountId = accountId, balance = balance, availableBalance = availableBalance, currency = currency))


def templateOperationInfo(data):

    operationid = ''
    sourceamount = ''
    sourcecurrencycode = ''
    created = ''
    targettransaction = ''
    sourceaccountid = ''

    operationid = data.id

    for element in data.attribute:
        if (element.key == 'sourceamount'):
            sourceamount = element.value

        if (element.key == 'sourcecurrencycode'):
            sourcecurrencycode = element.value

        if (element.key == 'created'):
            created = element.value

        if (element.key == 'targettransaction'):
            targettransaction = element.value

        if (element.key == 'sourceaccountid'):
            sourceaccountid = element.value

    template = [
    "<h1>Operation info:</h1>",
    "<ul>",
        "<li><b>Source account ID:</b> {sourceaccountid}</li>",
        "<li><b>Operation ID:</b> {operationid}</li>",
        "<li><b>Source amount:</b> {sourceamount}</li>",
        "<li><b>Source currency:</b> {sourcecurrencycode}</li>",
        "<li><b>Date created:</b> {created}</li>",
        "<li><b>Target transaction:</b> {targettransaction}</li>",
    "</ul>"
    ]

    return(render(template, sourceamount = sourceamount, operationid = operationid, sourcecurrencycode = sourcecurrencycode, 
                  created = created, targettransaction = targettransaction, sourceaccountid = sourceaccountid))


def templateProfileInfo(data):
    
    fio_contact = ''
    tariff = ''
    registration_date_ru = ''
    url = ''
    inn = ''
    unitid = ''
    profileType = ''
    name = ''
    organization_name = ''
    fio_accountant = ''
    contact_email = ''
    typeid = ''
    parentid = ''
    profileid = ''
    
    for element in data:
        if (element.key == 'fio_contact'):
            fio_contact = element.value
            
        if (element.key == 'tariff'):
            tariff = element.value
            
        if (element.key == 'registration_date_ru'):
            registration_date_ru = element.value
            
        if (element.key == 'url'):
            url = element.value
            
        if (element.key == 'inn'):
            inn = element.value
            
        if (element.key == 'unitid'):
            unitid = element.value
            
        if (element.key == 'profileType'):
            profileType = element.value
            
        if (element.key == 'name'):
            name = element.value
             
        if (element.key == 'organization_name'):
            organization_name = element.value
             
        if (element.key == 'fio_accountant'):
            fio_accountant = element.value

        if (element.key == 'contact_email'):
            contact_email = element.value
             
        if (element.key == 'typeid'):
            typeid = element.value
             
        if (element.key == 'parentid'):
            parentid = element.value
             
        if (element.key == 'profileid'):
            profileid = element.value

    template = [
    "<h1>Profile info:</h1>",
    "<ul>",
        "<li><b>Business name:</b> {name}</li>",
        "<li><b>Organization name:</b> {organization_name}</li>",
        "<li><b>Contact person:</b> {fio_contact}</li>",
        "<li><b>Accountant:</b> {fio_accountant}</li>",
        "<li><b>Contact e-mail:</b> {contact_email}</li>",
        "<li><b>Registration date:</b> {registration_date_ru}</li>",
        "<li><b>Tarif:</b> {tariff}</li>",
        "<li><b>Profile type:</b> {profileType}</li>",
        "<li><b>Url:</b> {url}</li>",
        "<li><b>Inn:</b> {inn}</li>",
        "<li><b>Unit ID:</b> {unitid}</li>",
        "<li><b>Type ID:</b> {typeid}</li>",
        "<li><b>Parent ID:</b> {parentid}</li>",
        "<li><b>Profile ID:</b> {profileid}</li>",
    "</ul>"
    ]
    
    return(render(template, fio_contact = fio_contact, tariff = tariff, registration_date_ru = registration_date_ru, url = url,
                  inn = inn, unitid = unitid, profileType = profileType, name = name, organization_name = organization_name,
                  fio_accountant = fio_accountant, contact_email = contact_email, typeid = typeid, parentid = parentid,
                  profileid = profileid))

