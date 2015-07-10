"""
	Kite REST API client
"""
import json
import requests

import exceptions as ex

class Kite:
	# root API url
	_root = "http://localhost:8000"

	# URIs to various calls
	_routes = {
		"login": "/user/login",
		"2fa": "/user/2fa",
		"logout": "/user/logout",
		"profile": "/user/profile",
		"password": "/user/password",
		"transpassword": "/user/transpassword",
		"margins": "/user/margins/{segment}",
		"session_hash": "/user/session_hash",

		"orders": "/orders",
		"order_info": "/orders/{order_id}",
		"order_modify": "/orders/{order_id}",
		"order_cancel": "/orders/{order_id}",
		"amo_place": "/amo",
		"amo_modify": "/amo/{order_id}",
		"amo_cancel": "/amo/{order_id}",

		"orders": "/orders",
		"order": "/orders/{order_id}",
		"trades": "/trades",

		"positions": "/positions",
		"holdings": "/holdings",
		"holdings_t1": "/holdings/t1",
		"product_modify": "/positions",

		"scrips": "/scrips/{exchange}",
		"quote": "/quote/{exchange}/{tradingsymbol}",

		"messages_admin": "/messages/admin",
		"messages_exchange": "/messages/exchange"
	}

	timeout = 7
	_session_hook = None

	def __init__(self, user_id, token=None, root=None, debug=False, timeout = 7):
		self.user_id = user_id
		self.token = token
		self.debug = debug
		self.timeout = timeout

		if root:
			self.root = root

	def session_hook(self, method):
		"""
		A callback hook for session timeout errors.
		A token (login session) can become invalid for a number of
		reasons, but it doesn't make sense for the client to
		try and catch it during every API call.

		A callback that handles session timeout errors
		can be provided here and when the client encounters
		a token error, it'll be called.

		This callback, for instance, can log the user out of the UI,
		clear session cookies, or show a timeout error message
		"""
		self._session_hook = method

	def set_token(self, token):
		"""
		Set the access token received after successful login.
		After the first login, this token should be saved in the
		session somewhere and passed to the client for further
		API calls.
		"""
		self.token = token

	def login(self, password, ip):
		"""
		Authenticate the user's credentials.
		If the system has 2FA enabled, the questions are returned

		Args:
			password: user's password
			ip: IP address of the user

		Raises:
			UserException: if the login fails
		"""
		return self._post("login", {"password": password, "ip": ip})

	def do2fa(self, qa):
		"""
		Do 2FA authentication and login

		Args:
			qa: dict of question_id received from the login() call
				  and corresponding answer received from the user

		Raises:
			TwoFAException: if the user has entered the wrong answers
			UserException: if 2FA failures exceed and the account is blocked
		"""
		params = {"question[]": [], "answer[]": []}

		for question in qa:
			params["question[]"].append(question)
			params["answer[]"].append(qa[question])

		return self._post("2fa", params)

	def update_2fa(self, qa):
		"""
		Set the user's choice of 2FA questions and answers

		Args:
			qa: dict of question_id received from the login() call
				and corresponding answer received from the user

		Raises:
			UserException: if the updation failed
		"""
		params = {"question[]": [], "answer[]": []}

		for question in qa:
			params["question[]"].append(question)
			params["answer[]"].append(qa[question])

		return self._put("2fa", params)

	def reset_2fa(self, email, identification):
		"""
		Reset the user's 2FA questions and answers so they're
		prompted for a fresh set during the next login

		Args:
			email: account email
			identification: the required form of identification (eg: PAN)

		Raises:
			TwoFAException: if the update fails for some reason
		"""
		params = {"email": email, "identification": identification}

		return self._delete("2fa", params)

	def session_hash(self):
		"""
		Generates a session hash for non-login routines such as
		payment gateway authentication
		"""

		return self._get("session_hash")

	def logout(self):
		"""Log the user out by invalidating the token"""
		return self._post("logout")

	# user
	def profile(self):
		"""
		Fetch the user's profile

		Returns:
			{
				dp_ids: [002178],
				user_id: DM0002,
				name: DM0002,
				bank_accounts: [{	account: 083311600,
									name: HDFC BANK LTD,
									branch: JAKKASANDRA}],
				phone: 98362716273,
				email: test@zerodha.com,
				pan: BPALQ5996K,
			}

		Raises:
			UserException: if the profile fetching failed
		"""
		return self._get("profile")

	def password_update(self, old_password, new_password):
		"""Change the login password"""
		return self._put("password", {
					"old_password": old_password,
					"new_password": new_password
				})

	def transpassword_update(self, old_password, new_password):
		"""Change the transaction password"""
		return self._put("transpassword", {
					"old_password": old_password,
					"new_password": new_password
				})

	def transpassword_check(self, password):
		"""Check the transaction password"""
		return self._post("transpassword", {
					"password": password
				})

	def reset_password(self, email, identification):
		"""
		Reset the user's primary password

		Args:
			email: account email
			identification: the required form of identification (eg: PAN)

		Raises:
			TwoFAException: if the update fails for some reason
		"""
		params = {"email": email, "identification": identification}

		return self._delete("password", params)

	def margins(self, segment):
		"""
			Get account balance and cash margin details

			Args:
				segment: should be either 'equity' or 'commodity'

			Returns:
				{
					net: 25000.00,
					available: {
						adhoc_margin: 0.00,
						collateral: 0.00,
						intraday_payin: 0.00,
						cash: 25000.00,
					},
					utilised: {
						category: EQUITY,
						span: 0.00,
						exposure: 0.00,
						m2m_realised: -0.00,
						m2m_unrealised: -0.00,
						turnover: 0.00,
						option_premium: 0.00,
						holding_sales: 0.00
					}
				}

		"""
		return self._get("margins", {"segment": segment})

	# orders
	def order_info(self, order_id):
		"""
		Get the history of an individual order

		Args:
			order_id: NEST order id

		Returns:
			[{   average_price: 0,
				disclosed_quantity: 0,
				exchange: NSE,
				exchange_order_id: 2014111971512657,
				order_id: 141119000062604,
				order_timestamp: 2014-11-19 15:19:48,
				order_type: LIMIT,
				pending_quantity: 1,
				price: 950,
				quantity: 1,
				status: cancel pending,
				status_message: None,
				tradingsymbol: RELIANCE,
				transaction_type: BUY,
				trigger_price: 0,
				validity: DAY
			}
			... more statuses
			]
		"""
		return self._get("order_info", {"order_id": order_id})

	def order_place(self, exchange, tradingsymbol, transaction_type,
					order_type, quantity, price, product,
					validity="DAY", disclosed_quantity=0,
					trigger_price=0,
					):
		"""
		Place an order and return the NEST order number if successful

		Args:
			exchange: NSE, BSE, NFO, BFO, MCX, MCXSX
			tradingsymbol: full trading symbol, eg: NIFTY14DEC8200CE
			transaction_type: BUY or SELL
			quantity: integer quantity
			price: float price (0 if market order)
			order_type: SL, SL-M, LIMIT, MARKET
			validity: DAY, IOC, GTC, GTD
			disclosed_quantity: 0 or the same as quantity
			trigger_price: only for SL (stoploss orders)
		"""
		return self._post("orders", {
			"exchange": exchange,
			"tradingsymbol": tradingsymbol,
			"transaction_type": transaction_type,
			"quantity": quantity,
			"price": price,
			"order_type": order_type,
			"trigger_price": trigger_price,
			"disclosed_quantity": disclosed_quantity,
			"product": product,
			"validity": validity
		})["order_id"]

	def order_modify(self, order_id, exchange, tradingsymbol, transaction_type,
					quantity, price, order_type, product,
					validity="DAY", disclosed_quantity=0,
					trigger_price=0,
					):
		"""
		Modify an order and return the NEST order number if successful

		Args:
			order_id: NEST order id of the existing order
			Rest of the parameters are same as order_place
		"""
		return self._put("order_modify", {
			"order_id": order_id,
			"exchange": exchange,
			"tradingsymbol": tradingsymbol,
			"transaction_type": transaction_type,
			"quantity": quantity,
			"price": price,
			"order_type": order_type,
			"trigger_price": trigger_price,
			"disclosed_quantity": disclosed_quantity,
			"product": product,
			"validity": validity
		})["order_id"]

	def order_cancel(self, order_id):
		"""Cancel an order"""
		return self._delete("order_cancel", {"order_id": order_id})["order_id"]

	# amo
	def amo_place(self, exchange, tradingsymbol, transaction_type,
					quantity, price, order_type, product,
					validity="DAY", disclosed_quantity=0,
					trigger_price=0
					):
		"""Place an after market order and return the NEST order number if successful"""
		return self._post("amo_place", {
			"exchange": exchange,
			"tradingsymbol": tradingsymbol,
			"transaction_type": transaction_type,
			"quantity": quantity,
			"price": price,
			"order_type": order_type,
			"trigger_price": trigger_price,
			"disclosed_quantity": disclosed_quantity,
			"product": product,
			"validity": validity
		})["order_id"]

	def amo_modify(self, order_id, exchange, tradingsymbol, transaction_type,
					quantity, price, order_type, product,
					validity="DAY", disclosed_quantity=0,
					trigger_price=0):
		"""Modify an after market order and return the NEST order number if successful"""
		return self._put("amo_modify", {
			"order_id": order_id,
			"exchange": exchange,
			"tradingsymbol": tradingsymbol,
			"transaction_type": transaction_type,
			"quantity": quantity,
			"price": price,
			"order_type": order_type,
			"trigger_price": trigger_price,
			"disclosed_quantity": disclosed_quantity,
			"product": product,
			"validity": validity
		})["order_id"]

	def amo_cancel(self, order_id):
		"""Cancel an after market order"""
		return self._delete("amo_cancel", {"order_id": order_id})["order_id"]

	# orderbook and tradebook
	def orders(self):
		"""
		Get the collection of orders from the orderbook

		Returns:
			[{  account_id: DM0002,
				average_price: 0,
				disclosed_quantity: 0,
				duration: DAY,
				exchange: NSE,
				exchange_order_id: None,
				exchange_timestamp: None,
				filled_quantity: 0,
				market_protection: 0,
				order_id: 141119000078269,
				order_timestamp: 2014-11-19 17:36:47,
				order_type: LIMIT,
				pending_quantity: 0,
				price: 95000,
				product: MIS,
				quantity: 1,
				status: rejected,
				status_message: Admin stopped AMO,
				symbol: RELIANCE,
				tradingsymbol: RELIANCE-EQ,
				transaction_type: BUY,
				user_id: DM0002
		   } ... ]
		"""
		return self._get("orders")

	def trades(self):
		"""
		Get the collection of executed trades (tradebook)

		Returns:
			[{
				order_id
				trade_id
				order_timestamp
				exchange_order_id
				exchange_timestamp

				tradingsymbol
				symbol
				exchange

				transaction_type
				average_price
				filled_quantity

				product
			} ... ]
		"""
		return self._get("trades")

	# positions and holdings
	def positions(self):
		"""
		Get the list of positions
		"""
		return self._get("positions")

	def holdings(self):
		"""
		Get the list of demat holdings

		Returns:
			[
				{
					product: CNC,
					account_id: DM1594,
					price: 0.0,
					last_price: 961.6,
					collateral_quantity: 0,
					collateraltype: None,
					tradingsymbol: RELIANCE-EQ,
					t1_quantity: 5,
					quantity: 0
				}
				...
			]
		"""
		return self._get("holdings")

	def holdings_t1(self):
		"""
		Get the list of demat holdings

		Returns:
			[
				{
					product: CNC,
					quantity: 5,
					tradingsymbol: RELIANCE-EQ,
					account_id: DM1594
				}
			]
		"""
		return self._get("holdings_t1")

	def product_modify(self, exchange, tradingsymbol, transaction_type, quantity, 
						old_product, new_product):
		"""Modify a position's product type"""
		return self._put("product_modify", {
			"exchange": exchange,
			"tradingsymbol": tradingsymbol,
			"transaction_type": transaction_type,
			"quantity": quantity,
			"old_product": old_product,
			"new_product": new_product
		})

	# scrips
	def scrips(self, exchange, search=None):
		"""
		Get list of scrips by exchange with optional substring search

		Args:
			exchange: NSE, BSE ...
			search: search string, eg: RELIANCE. If no search string
				is specified, the API will attempt to return all
				scrips in the segment which could be disastrous

		Returns:
			[   {   isin: INE036A01016,
					lot_size: 1,
					name: RELIANCE INFRASTRUCTU LTD,
					symbol_code: 12711,
					tradingsymbol: RELINFRA-BL
				},
				{   isin: INE036A01016,
					lot_size: 1,
					name: RELIANCE INFRASTRUCTU LTD,
					symbol_code: 553,
					tradingsymbol: RELINFRA-EQ
				} ... ]

		"""
		params = {"exchange": exchange}

		if search:
			params["search"] = search

		return self._get("scrips", params)

	def quote(self, exchange, tradingsymbol):
		"""
		Get quote and market depth for an instrument

		Returns:
			{   name: FUTCOM-GOLD,
				symbol: GOLD,
				buys: 722,
				sells: 751,
				change: 0.39,
				change_percent: 106.0,
				depth: {   buy: [   {   orders: 1, price: 26706.0, quantity: 1},
									{   orders: 1, price: 26705.0, quantity: 1},
										  ...
							],
							  sell: [   {   orders: 1, price: 26713.0, quantity: 1},
										{   orders: 2, price: 26714.0, quantity: 2},
										  ...
							]
						},
				last_price: 26702.0,
				last_quantity: 1,
				last_time: 2014-11-19 20:40:55,
				ohlc: { close: 26596.0,
						high: 26810.0,
						low: 26553.0,
						open: 26575.0},
				open_interest: 9066,
				series: None,
				volume: 12899
			}
		"""
		return self._get("quote", {"exchange": exchange, "tradingsymbol": tradingsymbol})

	# messages
	def messages_admin(self):
		"""
		Get messages posted by the admin

		Returns:
		[
			{"message": "Message 1 here"},
			{"message": "Message 2 here"}
			...
		]
		"""
		return self._get("messages_admin")

	def messages_exchange(self):
		"""
		Get messages posted by the admin

		Returns:
		[
			{"exchange": "NSE", "message": "Message 1 here"},
			{"exchange": "MCX", "message": "Message 2 here"}
			...
		]
		"""
		return self._get("messages_exchange")

	# __ private methods
	def _get(self, route, params={}):
		"""Alias for sending a GET request"""
		return self._request(route,
							"GET",
							params)

	def _post(self, route, params={}):
		"""Alias for sending a POST request"""
		return self._request(route,
							"POST",
							params)

	def _put(self, route, params={}):
		"""Alias for sending a PUT request"""
		return self._request(route,
							"PUT",
							params)

	def _delete(self, route, params={}):
		"""Alias for sending a DELETE request"""
		return self._request(route,
							"DELETE",
							params)

	def _request(self, route, method, params={}):
		"""Make an HTTP request"""

		# user id has to go with every request
		params["user_id"] = self.user_id

		# is there  atoken?
		if self.token:
			params["token"] = self.token

		uri = self._routes[route]

		# 'RESTful' URLs
		if "{" in uri:
			for k in params:
				uri = uri.replace("{" + k + "}", str(params[k]))

		url = self._root + uri

		if self.debug:
			print "Request: ", url
			print params, "\n"

		try:
			r = requests.request(
					method,
					url,
					data=params if method == "POST" else None,
					params=params if method != "POST" else None,
					verify=False,
					allow_redirects=True,
					timeout=self.timeout
				)
		except requests.ConnectionError:
			raise ex.ClientNetworkException("Gateway connection error", code=503)
		except requests.Timeout:
			raise ex.ClientNetworkException("Gateway timed out", code=504)
		except requests.HTTPError:
			raise ex.ClientNetworkException("Invalid response from gatway", code=502)
		except Exception as e:
			raise ex.ClientNetworkException(e.message, code=500)

		if self.debug:
			print "Response :", r.status_code, r.content, "\n"

		# content types
		if r.headers["content-type"] == "application/json":
			try:
				data = json.loads(r.content)
			except:
				raise ex.DataException("Unparsable response")

			# api error
			if data["status"] == "error":
				if r.status_code == 403: # session / auth error
					if self._session_hook:
						self._session_hook()
						return

				# native Kite errors
				if data["error_type"] == "GeneralException":
					raise(ex.GeneralException(data["message"], code=r.status_code))

				elif data["error_type"] == "UserException":
					raise(ex.UserException(data["message"], code=r.status_code))

				elif data["error_type"] == "TwoFAException":
					raise(ex.TwoFAException(data["message"], questions=data["questions"], code=r.status_code))

				elif data["error_type"] == "OrderException":
					raise(ex.OrderException(data["message"], code=r.status_code))

				elif data["error_type"] == "GeneralException":
					raise(ex.GeneralException(data["message"], code=r.status_code))

				elif data["error_type"] == "InputException":
					raise(ex.InputException(data["message"], code=r.status_code))

				elif data["error_type"] == "DataException":
					raise(ex.DataException(data["message"], code=r.status_code))

				elif data["error_type"] == "NetworkException":
					raise(ex.NetworkException(data["message"], code=r.status_code))

				else:
					raise(ex.GeneralException(data["message"], code=r.status_code))

			return data["data"]
		# non json content (images for 2FA)
		elif r.headers["content-type"] in ("image/jpeg", "image/jpg"):
			return r.content
		else:
			raise ex.DataException("Invalid response format")
