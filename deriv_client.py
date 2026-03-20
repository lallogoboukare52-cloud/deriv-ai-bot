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
        # Étape 1 : Demander le proposal
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
            print(f"Erreur proposal: {proposal}")
            return None

        proposal_id = proposal["proposal"]["id"]

        # Étape 2 : Acheter le contrat
        await self.send({"buy": proposal_id, "price": str(stake)})
        buy_resp = await self.recv()

        if "buy" not in buy_resp:
            print(f"Erreur achat: {buy_resp}")
            return None

        contract_id = buy_resp["buy"]["contract_id"]
        buy_price = float(buy_resp["buy"]["buy_price"])
        print(f"Contrat acheté : ID={contract_id} | Mise={buy_price} USD")

        # Étape 3 : Attendre la fin du contrat et récupérer le vrai résultat
        result = await self.wait_for_result(contract_id, buy_price)
        return result

    async def wait_for_result(self, contract_id, buy_price):
        # Souscrire aux mises à jour du contrat
        await self.send({
            "proposal_open_contract": 1,
            "contract_id": contract_id,
            "subscribe": 1
        })

        max_attempts = 60  # max 60 secondes d'attente
        attempts = 0

        while attempts < max_attempts:
            resp = await self.recv()

            if "proposal_open_contract" in resp:
                contract = resp["proposal_open_contract"]
                status = contract.get("status", "")

                if status == "sold" or contract.get("is_expired", 0) == 1:
                    profit = float(contract.get("profit", 0))
                    sell_price = float(contract.get("sell_price", 0))
                    won = profit > 0

                    print(f"Contrat terminé : {'✅ GAGNÉ' if won else '❌ PERDU'} | PnL={profit:.2f} USD")

                    # Désabonner
                    await self.send({
                        "forget": resp.get("subscription", {}).get("id", "")
                    })

                    return {
                        "contract_id": contract_id,
                        "profit": profit,
                        "sell_price": sell_price,
                        "buy_price": buy_price,
                        "won": won
                    }

            attempts += 1
            await asyncio.sleep(1)

        # Timeout — récupérer manuellement
        print("Timeout attente résultat, récupération manuelle...")
        return await self.get_contract_result(contract_id, buy_price)

    async def get_contract_result(self, contract_id, buy_price):
        await self.send({
            "profit_table": 1,
            "contract_id": contract_id,
            "description": 1
        })
        resp = await self.recv()

        contracts = resp.get("profit_table", {}).get("transactions", [])
        if contracts:
            c = contracts[0]
            profit = float(c.get("sell_price", 0)) - float(c.get("buy_price", buy_price))
            return {
                "contract_id": contract_id,
                "profit": profit,
                "buy_price": buy_price,
                "won": profit > 0
            }

        return {"contract_id": contract_id, "profit": 0.0, "buy_price": buy_price, "won": False}

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
