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

    def _normalize_exchange_name(self, exchange_name: Any) -> str:
        if hasattr(exchange_name, "value"):
            exchange_name = getattr(exchange_name, "value")
        name = str(exchange_name or "").strip()
        if "." in name:
            name = name.rsplit(".", 1)[-1]
        return name.lower()

    def _get_exchange_adapter(self, exchange_name: str):
        adapter = self.exchange_registry.get(exchange_name)
        if not adapter:
            raise ValueError(f"Exchange {exchange_name} not supported")
        return adapter

    def get_exchange_adapter(self, exchange_name: str = ExchangeName.DERIBIT):
        return self._get_exchange_adapter(exchange_name)

    async def get_default_exchange_account(self, user_id: int, exchange_name: str = ExchangeName.DERIBIT) -> Optional[ExchangeAccount]:
        result = await self.db.execute(
            select(ExchangeAccount)
            .where(
                ExchangeAccount.user_id == user_id,
                ExchangeAccount.exchange_name == exchange_name,
                ExchangeAccount.disabled_at.is_(None),
            )
            .order_by(ExchangeAccount.created_at.desc())
        )
        return result.scalars().first()

    async def get_exchange_account(self, user_id: int, exchange_account_id: int) -> Optional[ExchangeAccount]:
        result = await self.db.execute(
            select(ExchangeAccount).where(
                ExchangeAccount.id == exchange_account_id,
                ExchangeAccount.user_id == user_id,
                ExchangeAccount.disabled_at.is_(None),
            )
        )
        return result.scalars().first()

    async def get_user_exchange_accounts(
        self,
        user_id: int,
        exchange_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = (
            select(ExchangeCredentials, ExchangeAccount)
            .join(ExchangeAccount, ExchangeCredentials.exchange_account_id == ExchangeAccount.id)
            .where(
                ExchangeCredentials.user_id == user_id,
                ExchangeCredentials.disabled_at.is_(None),
                ExchangeAccount.disabled_at.is_(None),
            )
            .order_by(ExchangeCredentials.created_at.desc())
        )
        if exchange_name:
            query = query.where(ExchangeAccount.exchange_name == exchange_name)
        result = await self.db.execute(query)
        rows = result.all()
        accounts: Dict[int, Dict[str, Any]] = {}
        for credentials, account in rows:
            if account.id in accounts:
                continue
            try:
                client_id = decrypt_data(credentials.encrypted_futures_api_key) if credentials.encrypted_futures_api_key else ""
            except Exception:
                client_id = ""
            label = account.label or (f"API {client_id[:6]}..." if client_id else f"Account {account.id}")
            accounts[account.id] = {
                "id": account.id,
                "exchange_name": self._normalize_exchange_name(account.exchange_name),
                "label": label,
                "client_id": client_id,
            }
        return list(accounts.values())

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
            select(ExchangeCredentials, ExchangeAccount)
            .join(ExchangeAccount, ExchangeCredentials.exchange_account_id == ExchangeAccount.id)
            .where(
                ExchangeCredentials.user_id == user_id,
                ExchangeCredentials.disabled_at.is_(None),
                ExchangeAccount.disabled_at.is_(None),
            )
            .order_by(ExchangeCredentials.created_at.desc())
        )
        rows = result.all()
        credentials_list = []
        for row, account in rows:
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
                    "exchange_name": self._normalize_exchange_name(row.exchange_name),
                    "label": account.label or "",
                    "client_id": client_id,
                    "masked_secret": masked_secret,
                }
            )
        return credentials_list

    async def save_credentials(
        self,
        user_id: int,
        api_key: str,
        api_secret: str,
        exchange_name: str = ExchangeName.DERIBIT,
        label: str = "",
    ) -> None:
        clean_label = str(label or "").strip()
        if not clean_label:
            raise ValueError("Label is required.")
        existing_result = await self.db.execute(
            select(ExchangeCredentials)
            .where(
                ExchangeCredentials.user_id == user_id,
                ExchangeCredentials.exchange_name == exchange_name,
                ExchangeCredentials.disabled_at.is_(None),
            )
            .order_by(ExchangeCredentials.created_at.desc())
        )
        for row in existing_result.scalars().all():
            try:
                existing_key = decrypt_data(row.encrypted_futures_api_key) if row.encrypted_futures_api_key else ""
            except Exception:
                existing_key = ""
            try:
                existing_secret = decrypt_data(row.encrypted_futures_api_secret) if row.encrypted_futures_api_secret else ""
            except Exception:
                existing_secret = ""
            if existing_key and existing_secret and existing_key == api_key and existing_secret == api_secret:
                raise ValueError("Keys already connected.")

        try:
            adapter = self._get_exchange_adapter(exchange_name)
            await adapter.validate_credentials(api_key, api_secret)
        except Exception as e:
            raise ValueError(f"Credential validation error: {e}")
        
        account = ExchangeAccount(user_id=user_id, exchange_name=exchange_name, label=clean_label)
        self.db.add(account)
        await self.db.flush()
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

    async def update_credentials(
        self,
        user_id: int,
        credentials_id: int,
        api_key: str,
        api_secret: str,
    ) -> None:
        result = await self.db.execute(
            select(ExchangeCredentials, ExchangeAccount)
            .join(ExchangeAccount, ExchangeCredentials.exchange_account_id == ExchangeAccount.id)
            .where(
                ExchangeCredentials.id == credentials_id,
                ExchangeCredentials.user_id == user_id,
                ExchangeCredentials.disabled_at.is_(None),
                ExchangeAccount.disabled_at.is_(None),
            )
        )
        row = result.first()
        if not row:
            raise ValueError("Credentials not found.")
        credentials, account = row
        adapter = self._get_exchange_adapter(account.exchange_name)
        try:
            await adapter.validate_credentials(api_key, api_secret)
        except Exception as e:
            raise ValueError(f"Credential validation error: {e}")
        credentials.encrypted_futures_api_key = encrypt_data(api_key)
        credentials.encrypted_futures_api_secret = encrypt_data(api_secret)
        await self.db.commit()
