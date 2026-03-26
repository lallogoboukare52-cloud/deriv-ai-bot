import asyncio
import json
import websockets
import config

class DerivClient:
    WS_URL = "wss://ws.binaryws.com/websockets/v3?app_id={}"

    def __init__(self):
        self.ws = None
        self.balance = 0.0
        self.authorized = False
        self._req_id = 1

    async def connect(self):
        url = self.WS_URL.format(config.DERIV_APP_ID)
        self.ws = await websockets.connect(url)
        await self.authorize()

    async def authorize(self):
        await self.send({"authorize": config.DERIV_TOKEN})
        resp = await self.recv()
        if "authorize" in resp:
            self.authorized = True
            self.balance = resp["authorize"]["balance"]
        else:
            raise Exception("Autorisation Deriv echouee")

    async def get_candles(self, symbol, count=200, tf=60):
        await self.send({
            "ticks_history": symbol,
            "count": count,
            "end": "latest",
            "granularity": tf,
            "style": "candles"
        })
        resp = await self.recv()
        return resp.get("candles", [])

    async def buy_contract(self, contract_type, stake, duration, symbol):
        await self.send({
            "proposal": 1,
            "amount": str(stake),
            "basis": "stake",
            "contract_type": contract_type,
            "currency": "USD",
            "duration": duration,
            "duration_unit": config.DURATION_UNIT,
            "symbol": symbol
        })
        proposal = await self.recv()
        if "proposal" not in proposal:
            return None
        proposal_id = proposal["proposal"]["id"]
        await self.send({"buy": proposal_id, "price": str(stake)})
        result = await self.recv()
        buy_info = result.get("buy")
        if not buy_info:
            return None
        contract_id = buy_info.get("contract_id")
        await asyncio.sleep(duration + 2)
        await self.send({
            "proposal_open_contract": 1,
            "contract_id": contract_id,
            "subscribe": 0
        })
        contract = await self.recv()
        poc = contract.get("proposal_open_contract", {})
        profit = float(poc.get("profit", 0))
        buy_info["profit"] = profit
        return buy_info

    async def get_balance(self):
        await self.send({"balance": 1})
        resp = await self.recv()
        self.balance = resp["balance"]["balance"]
        return self.balance

    async def subscribe_ticks(self, symbol):
        await self.send({"ticks": symbol, "subscribe": 1})

    async def send(self, data):
        data["req_id"] = self._req_id
        self._req_id += 1
        await self.ws.send(json.dumps(data))

    async def recv(self):
        msg = await self.ws.recv()
        return json.loads(msg)

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
