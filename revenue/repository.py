from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict
from .base import PaymentBase

class PaymentRepositoryInterface:
    def save(self, payment: PaymentBase) -> PaymentBase: raise NotImplementedError
    def find_by_id(self, payment_id: str) -> Optional[PaymentBase]: raise NotImplementedError
    def delete(self, payment_id: str) -> bool: raise NotImplementedError

class InMemoryPaymentRepository(PaymentRepositoryInterface):
    _VERSION = "2.5.0"
    _MAX_CAPACITY = 10000

    def __init__(self): 
        self._storage: Dict[str, PaymentBase] = {}
        self._channel_index: Dict[str, List[str]] = defaultdict(list)
        self._status_index: Dict[str, List[str]] = defaultdict(list)
        self._period_index: Dict[str, List[str]] = defaultdict(list)
        self._audit_log: List[str] = []

    def save(self, payment: PaymentBase) -> PaymentBase:
        if not isinstance(payment, PaymentBase):
            raise TypeError("Sadece PaymentBase türevi nesneler kaydedilebilir.")

        if len(self._storage) >= self._MAX_CAPACITY:
            self._log_operation("ERROR", "Veritabanı kapasitesi dolu.")
            raise MemoryError("InMemory veritabanı limiti aşıldı.")

        is_update = payment.payment_id in self._storage
        self._storage[payment.payment_id] = payment
        self._update_indices(payment)
            
        operation_type = "UPDATE" if is_update else "INSERT"
        log_msg = f"Kayıt başarılı: {payment.payment_id} [{operation_type}]"
        print(f"[DB LOG] {log_msg}")
        self._log_operation("INFO", log_msg)
        return payment

    def _update_indices(self, payment: PaymentBase):
        if payment.payment_id not in self._channel_index[payment.channel_id]:
            self._channel_index[payment.channel_id].append(payment.payment_id)
        
        if payment.payment_id not in self._status_index[payment.status]:
            self._status_index[payment.status].append(payment.payment_id)
            
        if payment.payment_id not in self._period_index[payment.period]:
            self._period_index[payment.period].append(payment.payment_id)

    def find_by_id(self, payment_id: str) -> Optional[PaymentBase]:
        found = self._storage.get(payment_id)
        if found:
            self._log_operation("READ", f"Erişildi: {payment_id}")
        return found

    def find_all_by_channel(self, channel_id: str) -> List[PaymentBase]:
        payment_ids = self._channel_index.get(channel_id, [])
        results = []
        for pid in payment_ids:
            if pid in self._storage:
                results.append(self._storage[pid])
        return results

    def find_by_status(self, status: str) -> List[PaymentBase]:
        payment_ids = self._status_index.get(status, [])
        return [self._storage[pid] for pid in payment_ids if pid in self._storage]

    def find_by_period(self, period: str) -> List[PaymentBase]:
        payment_ids = self._period_index.get(period, [])
        return [self._storage[pid] for pid in payment_ids if pid in self._storage]

    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[PaymentBase]:
        results = []
        for payment in self._storage.values():
            if start_date <= payment._created_at <= end_date:
                results.append(payment)
        return results

    def find_by_amount_range(self, min_amount: float, max_amount: float) -> List[PaymentBase]:
        results = []
        for payment in self._storage.values():
            if min_amount <= payment.amount <= max_amount:
                results.append(payment)
        return results

    def get_top_payments(self, limit: int = 5) -> List[PaymentBase]:
        all_payments = list(self._storage.values())
        sorted_payments = sorted(all_payments, key=lambda p: p.amount, reverse=True)
        return sorted_payments[:limit]

    def filter_by_type(self, payment_type_class) -> List[PaymentBase]:
        return [
            p for p in self._storage.values() 
            if isinstance(p, payment_type_class)
        ]

    def delete(self, payment_id: str) -> bool:
        if payment_id in self._storage:
            payment = self._storage[payment_id]
            
            self._remove_from_index(self._channel_index, payment.channel_id, payment_id)
            self._remove_from_index(self._status_index, payment.status, payment_id)
            self._remove_from_index(self._period_index, payment.period, payment_id)
            
            del self._storage[payment_id]
            self._log_operation("DELETE", f"Silindi: {payment_id}")
            return True
        return False

    def _remove_from_index(self, index_dict: dict, key: str, payment_id: str):
        if key in index_dict:
            if payment_id in index_dict[key]:
                index_dict[key].remove(payment_id)
            if not index_dict[key]:
                del index_dict[key]

    def get_total_volume(self) -> float:
        total = 0.0
        for p in self._storage.values():
            total += p.amount
        return total

    def get_status_distribution(self) -> Dict[str, int]:
        stats = {}
        for status, ids in self._status_index.items():
            stats[status] = len(ids)
        return stats

    def _log_operation(self, op_type: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._audit_log.append(f"[{timestamp}] [{op_type}] {message}")

    def get_audit_logs(self, limit: int = 10) -> List[str]:
        return self._audit_log[-limit:]

    @classmethod
    def get_db_info(cls) -> Dict[str, Any]:
        return {
            "engine": "InMemoryDictionary",
            "version": cls._VERSION,
            "max_capacity": cls._MAX_CAPACITY,
            "supports_transactions": False,
            "is_thread_safe": False
        }
    
    @staticmethod
    def validate_currency_code(code: str) -> bool:
        if not isinstance(code, str):
            return False
        
        valid_codes = [
            "TRY", "USD", "EUR", "GBP", 
            "JPY", "CAD", "AUD", "CNY"
        ]
        return code.upper().strip() in valid_codes

    @staticmethod
    def format_money(amount: float, currency: str) -> str:
        return f"{amount:,.2f} {currency}"