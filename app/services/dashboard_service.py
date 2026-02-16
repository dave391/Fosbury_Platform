from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from typing import Dict, Any, Optional, List
from datetime import date

from app.services.strategy_service import StrategyService
from core.models import StrategyPosition, ExchangeAccount

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.strategy_service = StrategyService(db)

    def build_equity_chart(
        self,
        snapshots: List[Any],
        width: int = 640,
        height: int = 220,
        padding: int = 20,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        min_date: Optional[date] = None,
        max_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        if not snapshots:
            return {"points": "", "width": width, "height": height, "min": 0.0, "max": 0.0}
        
        values = [s["equity_usdc"] if isinstance(s, dict) else s.equity_usdc for s in snapshots]
        min_value = min_value if min_value is not None else min(values)
        max_value = max_value if max_value is not None else max(values)
        
        if max_value == min_value:
            max_value = min_value + 1
            
        if min_date is None or max_date is None:
            snapshot_dates = [
                s["snapshot_date"] if isinstance(s, dict) else s.snapshot_date for s in snapshots
            ]
            if snapshot_dates:
                if min_date is None:
                    min_date = min(snapshot_dates)
                if max_date is None:
                    max_date = max(snapshot_dates)
        use_dates = min_date is not None and max_date is not None
        count = len(values)
        step = 0 if count == 1 else (width - padding * 2) / (count - 1)
        points = []
        
        for idx, snap in enumerate(snapshots):
            if use_dates:
                snap_date = snap["snapshot_date"] if isinstance(snap, dict) else snap.snapshot_date
                total_days = (max_date - min_date).days
                delta_days = (snap_date - min_date).days if snap_date else 0
                ratio_days = 0 if total_days <= 0 else (delta_days / total_days)
                x = padding + ratio_days * (width - padding * 2)
            else:
                x = padding + step * idx
            equity_value = snap["equity_usdc"] if isinstance(snap, dict) else snap.equity_usdc
            ratio = (equity_value - min_value) / (max_value - min_value)
            y = height - padding - ratio * (height - padding * 2)
            points.append(f"{x:.1f},{y:.1f}")
            
        return {
            "points": " ".join(points),
            "width": width,
            "height": height,
            "min": min_value,
            "max": max_value,
        }

    def _resolve_selected_strategy(self, active_strategies: List[Any], filter_strategy_id: Optional[int]):
        if filter_strategy_id:
            for strategy in active_strategies:
                if strategy.id == filter_strategy_id:
                    return strategy
        return None

    def _build_base_metrics(self, active_strategies: List[Any], selected_strategy, today: date) -> Dict[str, Any]:
        metrics = {
            "asset": None,
            "days_active": 0,
            "allocated_capital_usdc": 0.0,
            "current_capital_usdc": 0.0,
            "pnl_usdc": 0.0,
            "apr_percent": 0.0,
        }
        if not active_strategies:
            return metrics
        if selected_strategy:
            days_active = max(1, (today - selected_strategy.created_at.date()).days + 1)
            metrics["asset"] = selected_strategy.asset
            metrics["days_active"] = days_active
            metrics["allocated_capital_usdc"] = selected_strategy.allocated_capital_usdc
        else:
            earliest_date = min(strategy.created_at.date() for strategy in active_strategies)
            days_active = max(1, (today - earliest_date).days + 1)
            metrics["asset"] = "Aggregate"
            metrics["days_active"] = days_active
            metrics["allocated_capital_usdc"] = sum(
                strategy.allocated_capital_usdc for strategy in active_strategies
            )
        return metrics

    def _apply_current_metrics(self, metrics: Dict[str, Any], selected_strategy, strategy_stats: Dict[int, Any]) -> Dict[str, Any]:
        if selected_strategy and selected_strategy.id in strategy_stats:
            metrics["current_capital_usdc"] = strategy_stats[selected_strategy.id]["current_capital"]
            metrics["pnl_usdc"] = strategy_stats[selected_strategy.id]["pnl_usdc"]
            if metrics["allocated_capital_usdc"] > 0 and metrics["days_active"] > 0:
                metrics["apr_percent"] = (metrics["pnl_usdc"] / metrics["allocated_capital_usdc"]) * (
                    365 / metrics["days_active"]
                ) * 100
        elif not selected_strategy:
            metrics["current_capital_usdc"] = sum(stat["current_capital"] for stat in strategy_stats.values())
            metrics["pnl_usdc"] = sum(stat["pnl_usdc"] for stat in strategy_stats.values())
            if metrics["allocated_capital_usdc"] > 0 and metrics["days_active"] > 0:
                metrics["apr_percent"] = (metrics["pnl_usdc"] / metrics["allocated_capital_usdc"]) * (
                    365 / metrics["days_active"]
                ) * 100
        return metrics

    def _shift_series(self, balance_snaps: List[Dict[str, Any]], series_values: List[float]):
        if not series_values:
            return balance_snaps, series_values
        offset = series_values[0]
        if offset != 0:
            series_values = [value - offset for value in series_values]
            balance_snaps = [
                {"snapshot_date": snap["snapshot_date"], "equity_usdc": value}
                for snap, value in zip(balance_snaps, series_values)
            ]
        return balance_snaps, series_values

    async def _build_equity_data(
        self,
        active_strategies: List[Any],
        selected_strategy,
        all_equity_snapshots: List[Any],
    ):
        equity_series = []
        equity_min = 0.0
        equity_max = 0.0
        equity_dates = []

        if not all_equity_snapshots:
            return equity_series, equity_min, equity_max, equity_dates

        grouped_deltas = {}
        for snap in all_equity_snapshots:
            pnl_delta = (snap.funding_delta_usdc or 0.0) - (snap.fees_delta_usdc or 0.0)
            grouped_deltas.setdefault(snap.snapshot_date, 0.0)
            grouped_deltas[snap.snapshot_date] += pnl_delta
        aggregate_deltas = [
            {"snapshot_date": snap_date, "delta_usdc": grouped_deltas[snap_date]}
            for snap_date in sorted(grouped_deltas.keys())
        ]

        series_by_strategy = {}
        for snap in all_equity_snapshots:
            series_by_strategy.setdefault(snap.strategy_id, []).append(snap)

        balance_values = []
        if selected_strategy:
            snaps = series_by_strategy.get(selected_strategy.id) or []
            snaps = sorted(snaps, key=lambda snap: snap.snapshot_date)
            if snaps:
                chart_min_date = snaps[0].snapshot_date
                chart_max_date = snaps[-1].snapshot_date
                pnl_total = 0.0
                balance_snaps = []
                series_values = []
                for snap in snaps:
                    pnl_delta = (snap.funding_delta_usdc or 0.0) - (snap.fees_delta_usdc or 0.0)
                    pnl_total += pnl_delta
                    balance_snaps.append({"snapshot_date": snap.snapshot_date, "equity_usdc": pnl_total})
                    series_values.append(pnl_total)
                balance_snaps, series_values = self._shift_series(balance_snaps, series_values)
                if series_values:
                    balance_values.extend(series_values)
                equity_series.append(
                    {
                        "key": str(selected_strategy.id),
                        "strategy_id": selected_strategy.id,
                        "label": selected_strategy.asset,
                        "chart": self.build_equity_chart(
                            balance_snaps,
                            min_date=chart_min_date,
                            max_date=chart_max_date,
                        ),
                        "values": series_values,
                        "dates": [snap["snapshot_date"].isoformat() for snap in balance_snaps],
                    }
                )
                equity_dates = [chart_min_date.isoformat(), chart_max_date.isoformat()]
        else:
            chart_min_date = min(snap.snapshot_date for snap in all_equity_snapshots)
            chart_max_date = max(snap.snapshot_date for snap in all_equity_snapshots)
            aggregate_balance = []
            series_values = []
            if aggregate_deltas:
                pnl_total = 0.0
                for snap in aggregate_deltas:
                    pnl_total += snap["delta_usdc"]
                    aggregate_balance.append({"snapshot_date": snap["snapshot_date"], "equity_usdc": pnl_total})
                    series_values.append(pnl_total)
                aggregate_balance, series_values = self._shift_series(aggregate_balance, series_values)
                if series_values:
                    balance_values.extend(series_values)
            equity_dates = [chart_min_date.isoformat(), chart_max_date.isoformat()]
            aggregate_chart = self.build_equity_chart(
                aggregate_balance,
                min_date=chart_min_date,
                max_date=chart_max_date,
            )
            equity_series.append(
                {
                    "key": "all",
                    "strategy_id": None,
                    "label": "All",
                    "chart": aggregate_chart,
                    "values": series_values if aggregate_deltas else [],
                    "dates": [snap["snapshot_date"].isoformat() for snap in aggregate_balance],
                }
            )

            for strategy in active_strategies:
                snaps = series_by_strategy.get(strategy.id)
                if not snaps:
                    continue
                snaps = sorted(snaps, key=lambda snap: snap.snapshot_date)
                pnl_total = 0.0
                balance_snaps = []
                series_values = []
                for snap in snaps:
                    pnl_delta = (snap.funding_delta_usdc or 0.0) - (snap.fees_delta_usdc or 0.0)
                    pnl_total += pnl_delta
                    balance_snaps.append({"snapshot_date": snap.snapshot_date, "equity_usdc": pnl_total})
                    series_values.append(pnl_total)
                balance_snaps, series_values = self._shift_series(balance_snaps, series_values)
                if series_values:
                    balance_values.extend(series_values)
                equity_series.append(
                    {
                        "key": str(strategy.id),
                        "strategy_id": strategy.id,
                        "label": strategy.asset,
                        "chart": self.build_equity_chart(
                            balance_snaps,
                            min_date=chart_min_date,
                            max_date=chart_max_date,
                        ),
                        "values": series_values,
                        "dates": [snap["snapshot_date"].isoformat() for snap in balance_snaps],
                    }
                )

        if balance_values:
            equity_min = min(balance_values)
            equity_max = max(balance_values)
            if equity_max == equity_min:
                equity_max = equity_min + 1
        for series in equity_series:
            series["chart"]["min"] = equity_min
            series["chart"]["max"] = equity_max

        return equity_series, equity_min, equity_max, equity_dates

    async def _build_historical_data(self, closed_strategies: List[Any], include_series: bool = True):
        closed_rows = []
        historical_metrics = {
            "count": 0,
            "pnl_usdc": 0.0,
            "apr_percent": 0.0,
            "fees_usdc": 0.0,
        }
        historical_series = []
        historical_min = 0.0
        historical_max = 0.0
        historical_dates = []
        if not closed_strategies:
            return (
                closed_rows,
                historical_metrics,
                historical_series,
                historical_min,
                historical_max,
                historical_dates,
            )

        closed_accounts_by_id = {}
        closed_account_ids = {strategy.exchange_account_id for strategy in closed_strategies}
        if closed_account_ids:
            closed_accounts_result = await self.db.execute(
                select(ExchangeAccount).where(ExchangeAccount.id.in_(closed_account_ids))
            )
            closed_accounts_by_id = {
                account.id: account for account in closed_accounts_result.scalars().all()
            }

        closed_ids = [strategy.id for strategy in closed_strategies]
        closures = await self.strategy_service.get_strategy_closures(closed_ids)
        closure_by_id = {closure.strategy_id: closure for closure in closures}

        positions_result = await self.db.execute(
            select(
                StrategyPosition.strategy_id,
                func.sum(StrategyPosition.allocated_capital_usdc).label("capital_total"),
            )
            .where(StrategyPosition.strategy_id.in_(closed_ids))
            .group_by(StrategyPosition.strategy_id)
        )
        capital_by_id = {
            row.strategy_id: float(row.capital_total or 0.0) for row in positions_result.all()
        }

        snapshots = await self.strategy_service.get_equity_snapshots(closed_ids)
        snapshot_totals = {}
        for snap in snapshots:
            stats = snapshot_totals.setdefault(snap.strategy_id, {"funding_total": 0.0, "fees_total": 0.0})
            stats["funding_total"] += snap.funding_delta_usdc or 0.0
            stats["fees_total"] += snap.fees_delta_usdc or 0.0

        cumulative_by_date = {} if include_series else None

        for strategy in closed_strategies:
            closure = closure_by_id.get(strategy.id)
            started_at = closure.started_at if closure else strategy.created_at
            closed_at = (
                closure.closed_at if closure else strategy.closed_at or strategy.updated_at or strategy.created_at
            )
            starting_capital = closure.starting_capital_usdc if closure else capital_by_id.get(strategy.id, 0.0)
            fees_usdc = closure.fees_usdc if closure else snapshot_totals.get(strategy.id, {}).get("fees_total", 0.0)
            if closure:
                pnl_usdc = closure.pnl_usdc
                final_capital = closure.final_capital_usdc
                apr_percent = closure.apr_percent
                days_active = closure.days_active
            else:
                funding_total = snapshot_totals.get(strategy.id, {}).get("funding_total", 0.0)
                realized_pnl = strategy.realized_pnl_usdc or 0.0
                pnl_usdc = realized_pnl + funding_total - fees_usdc
                days_active = max(1, (closed_at.date() - started_at.date()).days + 1)
                if starting_capital > 0 and days_active > 0:
                    apr_percent = (pnl_usdc / starting_capital) * (365 / days_active) * 100
                else:
                    apr_percent = 0.0
                final_capital = starting_capital + pnl_usdc

            exchange_account = closed_accounts_by_id.get(strategy.exchange_account_id)
            closed_rows.append(
                {
                    "start": started_at.date().isoformat(),
                    "stop": closed_at.date().isoformat(),
                    "name": strategy.name,
                    "exchange_name": exchange_account.exchange_name if exchange_account else None,
                    "asset": strategy.asset,
                    "starting_capital_usdc": starting_capital,
                    "final_capital_usdc": final_capital,
                    "pnl_usdc": pnl_usdc,
                    "fees_usdc": fees_usdc,
                    "apr_percent": apr_percent,
                }
            )

            if include_series:
                closed_date = closed_at.date()
                cumulative_by_date.setdefault(closed_date, 0.0)
                cumulative_by_date[closed_date] += pnl_usdc

            historical_metrics["count"] += 1
            historical_metrics["pnl_usdc"] += pnl_usdc
            historical_metrics["fees_usdc"] += fees_usdc

        if closed_rows:
            total_starting = sum(row["starting_capital_usdc"] for row in closed_rows)
            if total_starting > 0:
                weighted = sum(row["apr_percent"] * row["starting_capital_usdc"] for row in closed_rows)
                historical_metrics["apr_percent"] = weighted / total_starting
            else:
                historical_metrics["apr_percent"] = 0.0

        if include_series and cumulative_by_date:
            balance_snaps = []
            cumulative_total = 0.0
            series_values = []
            for snap_date in sorted(cumulative_by_date.keys()):
                cumulative_total += cumulative_by_date[snap_date]
                balance_snaps.append({"snapshot_date": snap_date, "equity_usdc": cumulative_total})
                series_values.append(cumulative_total)
            historical_dates = [snap["snapshot_date"].isoformat() for snap in balance_snaps]
            historical_series = [
                {
                    "key": "closed",
                    "strategy_id": None,
                    "label": "Closed",
                    "chart": self.build_equity_chart(balance_snaps),
                    "values": series_values,
                }
            ]
            if series_values:
                historical_min = min(series_values)
                historical_max = max(series_values)
                if historical_max == historical_min:
                    historical_max = historical_min + 1
            for series in historical_series:
                series["chart"]["min"] = historical_min
                series["chart"]["max"] = historical_max

        return (
            closed_rows,
            historical_metrics,
            historical_series,
            historical_min,
            historical_max,
            historical_dates,
        )

    async def get_dashboard_data(
        self,
        user_id: int,
        filter_strategy_id: Optional[int] = None,
        include_equity_series: bool = True,
        include_historical_series: bool = True,
    ) -> Dict[str, Any]:
        active_strategies = await self.strategy_service.get_active_strategies(user_id)
        today = date.today()
        selected_strategy = self._resolve_selected_strategy(active_strategies, filter_strategy_id)
        metrics = self._build_base_metrics(active_strategies, selected_strategy, today)
        active_rows = []
        equity_series = []
        equity_min = 0.0
        equity_max = 0.0
        equity_dates = []
        has_active = len(active_strategies) > 0
        scope_strategies = [selected_strategy] if selected_strategy else active_strategies
        strategy_stats = {}

        if has_active:
            all_strategy_ids = [strategy.id for strategy in active_strategies]
            rows_data = await self.strategy_service.build_active_strategy_rows(
                user_id,
                active_strategies,
                scope_strategies,
            )
            active_rows = rows_data.get("rows", [])
            strategy_stats = rows_data.get("strategy_stats", {})
            metrics = self._apply_current_metrics(metrics, selected_strategy, strategy_stats)
            if include_equity_series:
                all_equity_snapshots = await self.strategy_service.get_equity_snapshots(all_strategy_ids)
                (
                    equity_series,
                    equity_min,
                    equity_max,
                    equity_dates,
                ) = await self._build_equity_data(
                    active_strategies,
                    selected_strategy,
                    all_equity_snapshots,
                )
        
        table_rows = active_rows
        if selected_strategy:
            table_rows = [row for row in active_rows if row["id"] == selected_strategy.id]

        total_balance_usdc = sum(row["current_capital_usdc"] for row in active_rows) if active_rows else 0.0
        if selected_strategy:
            current_balance_usdc = metrics["current_capital_usdc"]
        else:
            current_balance_usdc = total_balance_usdc

        closed_strategies = await self.strategy_service.get_closed_strategies(user_id)
        (
            closed_rows,
            historical_metrics,
            historical_series,
            historical_min,
            historical_max,
            historical_dates,
        ) = await self._build_historical_data(closed_strategies, include_series=include_historical_series)

        return {
            "user_id": user_id,
            "active_strategies": active_rows,
            "table_rows": table_rows,
            "selected_strategy": selected_strategy,
            "metrics": metrics,
            "total_balance_usdc": total_balance_usdc,
            "current_balance_usdc": current_balance_usdc,
            "equity_chart": equity_series[0]["chart"] if equity_series else self.build_equity_chart([]),
            "equity_series": equity_series,
            "equity_min": equity_min,
            "equity_max": equity_max,
            "equity_dates": equity_dates,
            "has_active": has_active,
            "strategy_filter_id": selected_strategy.id if selected_strategy else None,
            "historical_rows": closed_rows,
            "historical_metrics": historical_metrics,
            "historical_series": historical_series,
            "historical_min": historical_min,
            "historical_max": historical_max,
            "historical_dates": historical_dates,
            
        }
