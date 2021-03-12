import requests
import json
import sys


class RegFoxAPI(object):
    """Python bindings for RegFox API

    `&pretty=true` can be added to most API requests, which formats JSON response for printing. Equivalent can be attained with python json formatting.

    Issues:
        Check-out endpoint calls the check-in endpoint, resulting in one way action. You can check in but never check out via API.

    Reference:
        https://docs.webconnex.io/api/v2/
    """

    url_base = 'https://api.webconnex.com/v2/public'
    endpoints = {
        'ping': '/ping',
        'search_orders': '/search/orders',
        'search_registrants': '/search/registrants',
        'registrant_checkin': '/registrant/check-in',
        'registrant_checkout': '/registrant/check-out',
        'search_transactions': '/search/transactions',
        'search_customers': '/search/customers',
        'list_global_coupons': '/coupons/global',
        'list_form_coupons': '/coupons/forms',
        'coupons': '/coupons',
        'forms': '/forms'
    }
    headers = {
        'apiKey': ''
    }
    default_api_path = 'config.json'
    strftime_iso_utc = "%Y-%m-%dT%H:%M:%SZ"

    last_request = None
    last_request_json = {}

    def __init__(self):
        super(RegFoxAPI, self).__init__()
        self.__load_api()

    def __load_api(self):
        with open(self.default_api_path) as f:
            config = json.load(f)
        self.headers['apiKey'] = config['api_key']

    """ Catch all API call """

    def __api_request(self, method:str, url:str, payload:dict=None, **kwargs:dict) -> requests.models.Response:
        """Constructs a GET request to specified API endpoint

        Regular API stuff like keys in the header are filled in.

        Params:
            Takes in full URL. Use for debugging or entering freeform URLs.
            If POST request, payload is JSON compatible dict
            GET params via kwargs supported.

        Returns:
            Raw response of the request
        """
        r = requests.request(method, url, headers=self.headers, json=payload, params=kwargs)
        self.last_request = r
        self.last_request_json = json.loads(r.text)
        return r

    def api_get(self, endpoint:str, **kwargs:dict) -> dict:
        """Constructs a GET request to specified API endpoint

        Params:
            API endpoint minus base URI
        Returns:
            Response as JSON interpreted dict
        """
        url = f"{self.url_base}{endpoint}"
        self.__api_request('GET', url, **kwargs)
        response = self.last_request_json
        return response

    # def get_json(self, endpoint:str) -> dict:
    #     """Same thing as get() but returns as JSON data"""
    #     r = self.api_get(endpoint)
    #     return r

    def api_post(self, endpoint:str, payload:dict, **kwargs:dict):
        """Same thing as get() but with POST requests

        Params:
            API endpoint minus base URI
            Data to send as POST payload
        Returns:
            Response as JSON interpreted dict
        """
        url = f"{self.url_base}{endpoint}"
        # data_string = json.dumps(data)  # regfox api and python requests fails unless json in string form
        self.__api_request('POST', url, payload=payload, **kwargs)
        response = self.last_request_json
        return response

    """ Pre-defined API calls"""

    def ping(self) -> dict:
        """Healthcheck to ensire API works"""
        return self.api_get(self.endpoints['ping'])

    """ Orders """

    def list_orders(self, form_id=None) -> dict:
        return self.search_orders(form_id=form_id)

    def search_orders(self, **kwargs:dict) -> dict:
        """Search for orders

        Params:
            Users kwargs. Any JSON key/value pair can be used as a function parameter. Examples below.

            order_id:
                numeric ID of order being serached for, 1234077

            formId:
                numeric ID of the registration page, 123410

            orderNumber:
                alphanumeric ID of the order, EXAMPLEEVENT202J98059V

            status:
                Pending
                Abandoned
                Completed
                # Pending Transfer - only for registrants
                # Transferred - only for registrants
                Waitlisted
                Canceled
                Pending offline payment

        Returns:
            All orders, unless a formId is specified, if so, orders for a specific page are returned.

            Sample:
                {'id': 1234567,
                 'displayId': '12345678DTYZBQG7P7S',
                 'customerId': 1234788,
                 'customerEmail': 'email@example.com',
                 'billing': {'firstName': 'First',
                  'lastName': 'Last',
                  'address': {'city': 'Example City',
                   'country': 'US',
                   'postalCode': '12345',
                   'state': 'CA',
                   'street1': '123 Example St.'}},
                 'formId': 123410,
                 'formName': 'Example Event Registration',
                 'formAccRef': 'EXAMPLEEVENT202',
                 'status': 'completed',
                 'orderNumber': 'EXAMPLEEVENT202J91234X',
                 'total': '112.00',
                 'currency': 'USD',
                 'metadata': None,
                 'dateCreated': '2019-07-21T06:16:19Z',
                 'dateUpdated': '2020-01-18T22:38:53Z'}
        """
        return self.api_get(self.endpoints['search_orders'], **kwargs)

    def search_orders_id(self, order_id:str) -> dict:
        """Search via numeric ID
        Params:
            ID from url when viewing a registrant, such as `1234567`
        """
        return self.api_get(f"{self.endpoints['search_orders']}/{order_id}")

    def search_orders_number(self, order_number:str) -> dict:
        """Search for an order by order number

        Params:
            Order Number that is pulled up on a transaction page, such as `EXAMPLEEVENT202J91234X`

        Returns:
            JSON of the order
        """
        return self.search_orders(orderNumber=order_number)

    """ Registrants """

    def list_registrants(self, form_id=None) -> dict:
        """List all registrants in system

        Params:
            Form ID to narrow down to registrations by specific reg page. See `list_forms()`
        """
        return self.search_registrants(form_id=form_id)

    def search_registrants(self, **kwargs) -> dict:
        """Search for registrants

        Note that API doesn't support searching for registrants via their `displayId`, or the ID shown on the registrants page, i.e. `12345678E3126ZQABCD`

        Returns:
            JSON of the registrant.

            Sample:
                {'id': 1230469,
                 'displayId': '12345678E3126ZQABCD',
                 'formId': 123410,
                 'formName': 'Example Event Registration',
                 'formAccRef': 'EXAMPLEEVENT202',
                 'orderCustomerId': 1234788,
                 'customerId': 1234788,
                 'orderId': 1234567,
                 'orderDisplayId': '12345ABCDEFGHIJKLM6',
                 'orderNumber': 'EXAMPLEEVENT202J91234X',
                 'orderEmail': 'email@example.com',
                 'status': 'completed',
                 'total': '112.00',
                 'amount': '112.00',
                 'currency': 'USD',
                 'fieldData': [{'label': 'Membership Levels',
                   'path': 'registrationOptions',
                   'value': 'option3'},
                  {'amount': '123',
                   'label': 'Another Example Option',
                   'path': 'registrationOptions.option3',
                   'value': 'true'}
                  { More Items From Registration Form ... }],
                 'metadata': None,
                 'checkedIn': True,
                 'dateCheckedIn': '2020-01-31T09:35:53.477545932Z',
                 'dateCreated': '2019-07-21T06:16:19Z',
                 'dateUpdated': '2020-01-08T03:37:52Z'}
        """
        return self.api_get(self.endpoints['search_registrants'], **kwargs)

    def search_registrants_number(self, reg_number:str) -> dict:
        """Search via numeric ID

        Params:
            ID from url when viewing a registrant, such as `1230469`
        """
        return self.api_get(f"{self.endpoints['search_registrants']}/{reg_number}")

    def registrant_checkin(self, reg_number:int=None, reg_id=None) -> dict:
        """Check in a user at a specified time

        Broken, see checkout function.

        Contrary to API docs, WebConnex will not use your timestamp in POST payload. Plus, in almost all practical use cases, timestamp should **not** be specified, it should be the current time to prevent retroactive and potentially integrity-breaking checkins.

        Params:
            reg_number is registrant's ID number, as an int and **not** a string. Alternatively, the reg ID can be used.

        Returns:
            reg_number, as well as the timestamp recorded for the check-in

            Sample:
                {"id":1230469,"date":"2020-01-31T09:04:56.538973464Z"}
        """
        assert type(reg_number) is int
        payload = {'id': reg_number}
        return self.api_post(self.endpoints['registrant_checkin'], payload=payload)

    def registrant_checkout(self, reg_number=None, reg_id=None) -> dict:
        """Check out a registrant after checking them in

        Currently broken as checking out a user will return the following

            {"responseCode":500,"error":{"code":8500,"description":"all ready checked in"}}\

        Regular users will be checked in if they haven't been already. Evidently, this endpoint is an alias for checkin.
        """
        assert type(reg_number) is int
        payload = {'id': reg_number}
        print('WARNING: checkout() is broken as of last test run', file=sys.stderr)
        return self.api_post(self.endpoints['registrant_checkout'], payload=payload)

    """ Transactions """

    def list_transactions(self, form_id=None):
        """List all transactions

        Params:
            form_id corresponding to the reg page to list transactions for
        """
        return self.search_transactions(formId=form_id)

    def search_transactions(self, **kwargs):
        """
        Params:
            status: completed, pending offline, declined, gateway error, etc.
                https://help.regfox.com/en/articles/2343634-transaction-statuses-explained
            type: charge, refund, voucher

        Returns:
            JSON of the transaction
            
            Sample:
                {'responseCode': 200,
                 'data': [{'id': 9876543,
                   'displayId': '9876543',
                   'formId': 123410,
                   'formName': 'Example Event Registration',
                   'formAccRef': 'EXAMPLEEVENT202',
                   'orderCustomerId': 1234788,
                   'customerId': 1234788,
                   'orderId': 1234567,
                   'orderDisplayId': '12345ABCDEFGHIJKLM6',
                   'orderNumber': 'EXAMPLEEVENT202J91234X',
                   'orderEmail': 'email@example.com',
                   'billing': {'firstName': 'First',
                    'lastName': 'Last',
                    'address': {'city': 'Example City',
                     'country': 'US',
                     'postalCode': '12345',
                     'state': 'CA',
                     'street1': '123 Example St.'}},
                   'transactionType': 'charge',
                   'total': '112.00',
                   'deductible': '0.00',
                   'currency': 'USD',
                   'paymentMethod': 'card',
                   'paymentType': 'VISA',
                   'paymentMask': 'VISA-1234',
                   'gatewayReference': '0123456789',
                   'status': 'completed',
                   'metadata': None,
                   'expMonth': 01,
                   'expYear': 2020,
                   'ccExpiration': '01/2020',
                   'dateCreated': '2019-07-21T06:16:19Z',
                   'dateUpdated': '2020-01-08T04:13:43Z'}],
                 'totalResults': 1}
        """
        return self.api_get(self.endpoints['search_transactions'], **kwargs)

    def search_transactions_order_id(self, order_id:int):
        """Search for transaction details via order's ID number.

        Note this pulls up all linked transactions

        Not used in regular workflow. Chances are we won't use this on human interfacing this.

        Params:
            Order number that shows up in URL for transaction page, i.e. 1234567 for https://manage.webconnex.com/a/1311/reports/orders/1234567/details/1230469
        """
        return self.search_transactions(orderId=order_id)

    def search_transactions_order_number(self, order_number:str) -> dict:
        """Search for transaction details using an order number

        Params:
            Order Number as per `search_orders_number()`, shows up as Order Number on transaction page, i.e. `EXAMPLEEVENT202J91234X`.
        """
        return self.search_transactions(orderNumber=order_number)

    def search_transactions_customer_id(self, customer_id:int) -> dict:
        """Search via customerId, only found via API

        Pulls up all historic purchases associated with registrant

        Params:
            customerId, see the customer functions. i.e. 1234788
        """
        return self.search_transactions(customerId=customer_id)

    """ Customers """

    def list_customers(self, form_id=None):
        return self.search_customers(formId=form_id)

    def search_customers(self, **kwargs):
        """Search for customer information, persistent across registration years.

        From WebConnex:
            Important Note: While a customer Id is assigned as time of registration; new customer records can take up to 5 minutes to be created and available in the Public API.

        Params:
            customerId, found only via API requests. It's part of the JSON object returned when searching for orders, registrants, and transactions. i.e. 1234788

        Returns:
            Sample:
                {'id': 1234788,
                 'displayId': '1234788',
                 'email': 'email@example.com',
                 'billing': {'firstName': 'First',
                  'lastName': 'Last',
                  'address': {'city': 'Example City',
                   'country': 'US',
                   'phone': '',
                   'postalCode': '12345',
                   'state': 'CA',
                   'street1': '123 Example St.',
                   'street2': ''}},
                 'dateCreated': '2017-09-26T04:52:39Z',
                 'dateUpdated': '2020-01-14T04:36:26Z'}
        """
        return self.api_get(self.endpoints['search_customers'], **kwargs)

    def search_customers_id(self, customer_id:int) -> dict:
        """Search for specific customer using their ID number"""
        return self.api_get(f"{self.endpoints['search_customers']}/{customer_id}")

    def search_customers_email(self, email:str) -> dict:
        """Appears to be broken at time of testing"""
        return self.search_customers(email=email)

    """ Forms """

    def list_forms(self) -> dict:
        """Equivalent to getting a listing of all pages.

        Returns:
            List with each element as a page in the regfox account. Seems to be chronological order.

            Sample:
                {'id': 223369,
                 'name': 'Example Event Registration',
                 'product': 'regfox.com',
                 'status': 'open',
                 'dateCreated': '2019-12-14T21:00:12Z',
                 'dateUpdated': '2020-01-21T07:35:38Z'}
        """
        return self.api_get(self.endpoints['forms'])

    def search_forms_id(self, form_id:int) -> dict:
        """Retrieves comprehensive info about a specific registration campaign page"""
        return self.api_get(f"{self.endpoints['forms']}/{form_id}")

    """ Coupons """

    # WebConnex doesn't allow you to create coupons via API??!!!

    def list_global_coupons(self, **kwargs) -> dict:
        """Returns list of all available coupons across all registration campaign pages

        Params:
            coupons: coupon code to search for
            limit: number to limit results returned by

        Returns:
            List of all coupons

            Sample:
                {'id': 946158,
                 'formId': 123410,
                 'name': 'example coupon here',
                 'currency': 'USD',
                 'available': None,
                 'redeemed': 2,
                 'productId': 4,
                 'discounts': [{'distribute': False,
                   'perTicket': False,
                   'value': '112',
                   'valueType': 'fixed'}],
                 'codes': [{'code': '123couponforexampleevent123',
                   'redeemed': 2,
                   'dateCreated': '2020-01-18T07:05:06Z',
                   'dateUpdated': '2020-01-18T08:28:26Z'}],
                 'dateCreated': '2020-01-18T06:44:37Z',
                 'dateUpdated': '2020-01-18T08:28:26Z'}
        """
        return self.api_get(self.endpoints['list_global_coupons'], **kwargs)

    def list_form_coupons(self, form_id:int) -> dict:
        """List of all coupons for a specific registration campaign page"""
        return self.api_get(f"{self.endpoints['list_form_coupons']}/{form_id}")

    def search_coupons(self, coupon_id:int):
        return self.api_get(f"{self.endpoints['coupons']}/{coupon_id}")

    """ Inventory """

    def search_inventory(self, form_id:int):
        """Searched a specific reg page for all reg options limited by a number of supply items

        Returns:
            List of qty/sold for each inventory item

            Sample:
                [{'path': 'registrants.registrationOptions.option2',
                  'name': 'RegistrationLevelHere',
                  'sold': 100,
                  'quantity': 120,
                  'dateCreated': '2020-01-06T05:54:45Z',
                  'dateUpdated': '2020-01-19T22:09:27Z'},
                 {'path': 'registrants.registrationOptions.option3',
                  'name': 'AnotherRegLevel',
                  'sold': 150,
                  'quantity': 200,
                  'dateCreated': '2020-01-06T05:54:45Z',
                  'dateUpdated': '2020-01-18T17:52:35Z'}]
        """
        return self.api_get(f"{self.endpoints['forms']}/{form_id}/inventory")

    """ Inactive API functions not used by us """

    def search_tickets(self) -> dict:
        return self.api_get('/search/tickets')

    def search_subscriptions(self) -> dict:
        return self.api_get('/search/subscriptions')

    def search_memberships(self):
        return self.api_get('/search/memberships')


regfox = RegFoxAPI()


def test_ping():
    r = regfox.ping()
    print(r)
    assert regfox.last_request.ok


def test_order():
    print('Retrieving the 10th order....')
    order = regfox.list_orders()['data'][10]
    print(order)

    print(f"Order had ID of {order['id']}. Retrieving order with matching ID...")
    print(regfox.search_orders_id(order['id'])['data'])

    print('Retrieving an order that was canceled...')
    print(regfox.search_orders(status='canceled')['data'][0])

    specific_ordernumber = 'EXAMPLEEVENT202J91234X'
    print('Searching by order number for specific order...')
    print(regfox.search_orders_number(specific_ordernumber)['data'][0])


def test_registrants():
    print('Retrieving the 10th registrant...')
    reg = regfox.list_registrants()['data'][10]
    print(reg)

    print('Searching for specific reg via reg number')
    reg_number = '1230469'
    print(regfox.search_registrants_number(reg_number))

    print('Searching via email')
    specific_reg = regfox.search_registrants(orderEmail='email@example.com', formId='123410')
    print(specific_reg)
    assert specific_reg['totalResults'] == 1
    specific_reg_number = specific_reg['data'][0]['id']
    specific_reg_id = specific_reg['data'][0]['displayId']
    print(specific_reg_number, specific_reg_id)

    print('Skipping check in/out testing')
    # print('Checking in...')
    # print(regfox.registrant_checkin(reg_number=specific_reg_number))
    # print('Checking out...')
    # print(regfox.registrant_checkout(reg_number=specific_reg_number))


def test_tickets():
    pass


def test_subscriptions():
    pass


def test_transactions():
    # Some known transactions
    transaction_order_number = 'EXAMPLEEVENT202J91234X'
    order_id = 1234567

    print('Listing all transactions and retrieving most recent one...')
    print(regfox.list_transactions()['data'][0])

    print('Searching via transaction id')
    print('pending...')
    # TODO

    print('Searching via order id')
    print(regfox.search_transactions_order_id(order_id)['data'])

    print('Searching via order number')
    print(regfox.search_transactions_order_number(transaction_order_number)['data'])

    print('searching via customer ID')
    print(regfox.search_transactions_customer_id(1234788)['data'])


def test_customers():
    # Some known transactions
    customer_id = 1234788
    email = 'email@example.com'

    print('Listing all customers and retrieving most recent...')
    print(regfox.list_customers()['data'][0])

    print('Searching via your customer ID')
    print(regfox.search_customers_id(customer_id))

    print('Skipping email testing')
    # print('Searching via email')
    # print(regfox.search_customers_email(email))


def test_memberships():
    pass


def test_forms():
    first_event = 123410
    second_event = 223369

    print('Listing all forms and selecting FC 2020 and 2021')
    print(regfox.list_forms()['data'][0:2])
    # print(regfox.search_forms_id(first_event))
    # print(regfox.search_forms_id(second_event))


def test_coupons():
    first_event = 123410

    print('Listing global coupons')
    print(regfox.list_global_coupons()['data'][0])

    print('Listing coupons for first_event')
    print(regfox.list_form_coupons(first_event)['data'][0])

    print('Searching for ID of nightbadge coupon')
    print(regfox.search_coupons(946158))


def test_inventory():
    first_event = 123410

    print('Listing inventory for first_event')
    print(regfox.search_inventory(first_event))


def test_webhooks():
    pass


def test_specific_reg():
    # reg_id = '12345678E3126ZQABCD'
    reg_number = '1230469'
    order_number = 'EXAMPLEEVENT202J91234X'
    # regfox.search_registrants(orderId=reg_id)['totalResults']  # not possible
    regfox.search_registrants_number(reg_number)['totalResults']
    regfox.search_orders(orderNumber=order_number)['totalResults']


def main():
    print('Running...')

    test_ping()
    test_order()
    test_registrants()
    test_tickets()
    test_subscriptions()
    test_transactions()
    test_customers()
    test_memberships()
    test_forms()
    test_coupons()
    test_inventory()
    test_webhooks()

    # test_specific_reg()

    print('Completed')


if __name__ == '__main__':
    main()
