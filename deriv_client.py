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
    await self.send({"proposal_open_contract": 1, "contract_id": contract_id, "subscribe": 0})
    contract = await self.recv()
    poc = contract.get("proposal_open_contract", {})
    profit = float(poc.get("profit", 0))
    buy_info["profit"] = profit
    return buy_info
