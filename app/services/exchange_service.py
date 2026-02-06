from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import ExchangeAccount, ExchangeCredentials
from core.security import decrypt_data, encrypt_data
from core.enums import ExchangeName
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timezone
from app.services.exchanges.registry import get_exchange_registry

class ExchangeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.exchange_registry = get_exchange_registry()

    def _get_exchange_adapter(self, exchange_name: str):
        adapter = self.exchange_registry.get(exchange_name)
        if not adapter:
            raise ValueError(f"Exchange {exchange_name} non supportato")
        return adapter

    def get_exchange_adapter(self, exchange_name: str = ExchangeName.DERIBIT):
        return self._get_exchange_adapter(exchange_name)

    async def get_default_exchange_account(self, user_id: int, exchange_name: str = ExchangeName.DERIBIT) -> Optional[ExchangeAccount]:
        result = await self.db.execute(
            select(ExchangeAccount)
            .where(ExchangeAccount.user_id == user_id, ExchangeAccount.exchange_name == exchange_name)
            .order_by(ExchangeAccount.created_at.desc())
        )
        return result.scalars().first()

    async def get_or_create_default_exchange_account(
        self, user_id: int, exchange_name: str = ExchangeName.DERIBIT
    ) -> ExchangeAccount:
        account = await self.get_default_exchange_account(user_id, exchange_name)
        if account:
            return account
        account = ExchangeAccount(user_id=user_id, exchange_name=exchange_name)
        self.db.add(account)
        await self.db.flush()
        return account

    async def get_credentials_for_account(self, exchange_account_id: int) -> Optional[Tuple[str, str]]:
        result = await self.db.execute(
            select(ExchangeCredentials)
            .where(
                ExchangeCredentials.exchange_account_id == exchange_account_id,
                ExchangeCredentials.disabled_at.is_(None),
            )
            .order_by(ExchangeCredentials.created_at.desc())
        )
        row = result.scalars().first()
        if not row:
            return None

        try:
            api_key = decrypt_data(row.encrypted_futures_api_key) if row.encrypted_futures_api_key else ""
        except Exception:
            api_key = ""

        try:
            api_secret = decrypt_data(row.encrypted_futures_api_secret) if row.encrypted_futures_api_secret else ""
        except Exception:
            api_secret = ""

        if not api_key or not api_secret:
            return None

        return api_key, api_secret

    async def get_exchange_client_by_account(self, exchange_account_id: int):
        result = await self.db.execute(
            select(ExchangeAccount).where(ExchangeAccount.id == exchange_account_id)
        )
        account = result.scalars().first()
        if not account:
            return None
        credentials = await self.get_credentials_for_account(account.id)
        if not credentials:
            return None
        api_key, api_secret = credentials
        adapter = self._get_exchange_adapter(account.exchange_name)
        return await adapter.get_client(api_key, api_secret)

    async def get_configured_exchanges(self, user_id: int) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(ExchangeCredentials)
            .where(
                ExchangeCredentials.user_id == user_id,
                ExchangeCredentials.disabled_at.is_(None),
            )
            .order_by(ExchangeCredentials.created_at.desc())
        )
        rows = result.scalars().all()
        credentials_list = []
        for row in rows:
            try:
                client_id = decrypt_data(row.encrypted_futures_api_key) if row.encrypted_futures_api_key else ""
            except Exception:
                client_id = ""
            
            try:
                secret = decrypt_data(row.encrypted_futures_api_secret) if row.encrypted_futures_api_secret else ""
            except Exception:
                secret = ""
                
            masked_secret = secret
            if len(secret) > 6:
                masked_secret = f"{secret[:3]}...{secret[-3:]}"
                
            created_at = row.created_at.isoformat() if row.created_at else ""
            credentials_list.append(
                {
                    "id": row.id,
                    "created_at": created_at,
                    "exchange_name": row.exchange_name or "",
                    "client_id": client_id,
                    "masked_secret": masked_secret,
                }
            )
        return credentials_list

    async def save_credentials(self, user_id: int, api_key: str, api_secret: str, exchange_name: str = ExchangeName.DERIBIT) -> None:
        try:
            adapter = self._get_exchange_adapter(exchange_name)
            await adapter.validate_credentials(api_key, api_secret)
        except Exception as e:
            raise ValueError(f"Errore validazione credenziali: {e}")
        
        account = await self.get_or_create_default_exchange_account(user_id, exchange_name)
        credentials = ExchangeCredentials(
            user_id=user_id,
            exchange_name=exchange_name,
            exchange_account_id=account.id,
        )
        self.db.add(credentials)
        credentials.encrypted_futures_api_key = encrypt_data(api_key)
        credentials.encrypted_futures_api_secret = encrypt_data(api_secret)
        
        await self.db.commit()

    async def delete_credentials(self, user_id: int, credentials_id: int) -> None:
        result = await self.db.execute(
            select(ExchangeCredentials)
            .join(ExchangeAccount, ExchangeCredentials.exchange_account_id == ExchangeAccount.id)
            .where(ExchangeCredentials.id == credentials_id, ExchangeAccount.user_id == user_id)
        )
        credentials = result.scalars().first()
        if credentials:
            credentials.disabled_at = datetime.now(timezone.utc)
            await self.db.commit()
