import json
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.strategies.base import StrategyAdapter
from app.services.strategies.hlp.rules import MIN_CAPITAL_USD
from app.services.strategies.hlp.rules import STRATEGY_KEY
from app.services.strategies.hlp.rules import STRATEGY_NAME
from app.services.strategies.hlp.rules import get_exchange_rules
from core.enums import StrategyStatus
from core.models import Strategy


class HLPStrategy(StrategyAdapter):
    key = STRATEGY_KEY
    name = STRATEGY_NAME
    HLP_VAULT_ADDRESS = "0xdfc24b077bc1425ad1dea75bcb6f8158e10df303"

    def get_allowed_assets(self, exchange_id: str) -> List[str]:
        return list(get_exchange_rules(str(exchange_id or "").strip().lower()).get("assets") or [])

    def get_min_capital(self) -> float:
        return float(MIN_CAPITAL_USD)

    async def fetch_usdc_balance(self, exchange, adapter) -> float:
        return await adapter.fetch_quote_balance(exchange, "USDC")

    async def get_snapshot_equity_usdc(
        self,
        exchange,
        adapter,
        strategy: Strategy,
        base_equity_usdc: float,
        funding_delta_usdc: float,
        fees_delta_usdc: float,
    ) -> float:
        _ = adapter
        _ = strategy
        _ = base_equity_usdc
        _ = funding_delta_usdc
        _ = fees_delta_usdc
        return float(await self._get_vault_equity(exchange))

    async def start(
        self,
        db: AsyncSession,
        exchange,
        user_id: int,
        exchange_account_id: int,
        asset: str,
        capital_usdc: float,
    ) -> Strategy:
        amount = float(capital_usdc)
        await self._vault_transfer(exchange, amount, True)
        equity = await self._get_vault_equity(exchange)
        strategy = Strategy(
            user_id=user_id,
            exchange_account_id=exchange_account_id,
            asset="USDC",
            strategy_key=self.key,
            name=self.name,
            status=StrategyStatus.ACTIVE,
            allocated_capital_usdc=amount,
            total_quantity=0.0,
            entry_spot_px=1.0,
            entry_perp_px=1.0,
            config={
                "vault_address": self.HLP_VAULT_ADDRESS,
                "vault_equity": float(equity),
                "deposited_usdc": float(amount),
            },
        )
        db.add(strategy)
        await db.flush()
        return strategy

    async def add(self, db: AsyncSession, exchange, strategy: Strategy, added_amount_usdc: float) -> Strategy:
        amount = float(added_amount_usdc)
        await self._vault_transfer(exchange, amount, True)
        strategy.allocated_capital_usdc = float(strategy.allocated_capital_usdc or 0.0) + amount
        equity = await self._get_vault_equity(exchange)
        config = dict(strategy.config or {})
        config["vault_address"] = self.HLP_VAULT_ADDRESS
        config["vault_equity"] = float(equity)
        config["deposited_usdc"] = float(strategy.allocated_capital_usdc or 0.0)
        strategy.config = config
        strategy.asset = "USDC"
        return strategy

    async def remove(self, db: AsyncSession, exchange, strategy: Strategy, remove_amount_usdc: float) -> float:
        amount = float(remove_amount_usdc)
        await self._vault_transfer(exchange, amount, False)
        remaining = float(strategy.allocated_capital_usdc or 0.0) - amount
        strategy.allocated_capital_usdc = max(0.0, remaining)
        equity = await self._get_vault_equity(exchange)
        config = dict(strategy.config or {})
        config["vault_address"] = self.HLP_VAULT_ADDRESS
        config["vault_equity"] = float(equity)
        config["deposited_usdc"] = float(strategy.allocated_capital_usdc or 0.0)
        strategy.config = config
        if strategy.allocated_capital_usdc <= 0:
            strategy.status = StrategyStatus.CLOSED
            strategy.total_quantity = 0.0
        return amount

    async def stop(self, db: AsyncSession, exchange, strategy: Strategy) -> float:
        allocated = float(strategy.allocated_capital_usdc or 0.0)
        equity = await self._get_vault_equity(exchange)
        if equity > 0:
            await self._vault_transfer(exchange, equity, False)
        strategy.realized_pnl_usdc = float(equity - allocated)
        strategy.status = StrategyStatus.CLOSED
        strategy.allocated_capital_usdc = 0.0
        strategy.total_quantity = 0.0
        config = dict(strategy.config or {})
        config["vault_address"] = self.HLP_VAULT_ADDRESS
        config["vault_equity"] = 0.0
        config["deposited_usdc"] = 0.0
        strategy.config = config
        return float(equity)

    async def _vault_transfer(self, exchange, amount_usdc: float, is_deposit: bool):
        nonce = exchange.milliseconds()
        usd_units = int(round(float(amount_usdc) * 1_000_000))
        action = {
            "type": "vaultTransfer",
            "vaultAddress": self.HLP_VAULT_ADDRESS,
            "isDeposit": bool(is_deposit),
            "usd": usd_units,
        }
        signature = exchange.sign_l1_action(action, nonce)
        request = {
            "action": action,
            "nonce": nonce,
            "signature": signature,
        }
        try:
            response = await exchange.privatePostExchange(request)
        except Exception as exc:
            message = str(exc or "").strip()
            if "{" in message and "}" in message:
                payload = message[message.find("{") : message.rfind("}") + 1]
                try:
                    parsed = json.loads(payload)
                    parsed_message = parsed.get("response") if isinstance(parsed, dict) else None
                    if parsed_message:
                        message = str(parsed_message)
                except Exception:
                    pass
            raise ValueError(message or "Vault transfer failed") from exc
        if not isinstance(response, dict):
            raise ValueError("Vault transfer failed")
        if response.get("status") != "ok":
            raise ValueError(response.get("response") or "Vault transfer failed")
        return response

    async def _get_vault_equity(self, exchange, vault_address: str = HLP_VAULT_ADDRESS) -> float:
        response = await exchange.publicPostInfo(
            {
                "type": "userVaultEquities",
                "user": getattr(exchange, "walletAddress", None),
            }
        )
        rows = response if isinstance(response, list) else []
        target = str(vault_address or "").strip().lower()
        for row in rows:
            if not isinstance(row, dict):
                continue
            current = str(row.get("vaultAddress") or "").strip().lower()
            if current != target:
                continue
            try:
                return float(row.get("equity") or 0.0)
            except (TypeError, ValueError):
                return 0.0
        return 0.0


__all__ = ["HLPStrategy"]
