from typing import List, Optional, Dict
from datetime import datetime
from .base import PaymentBase
from .implementations import AdRevenuePayment, MembershipRevenuePayment, SponsorshipPayment

class PaymentRepositoryInterface:
    pass

class InMemoryPaymentRepository(PaymentRepositoryInterface):
    
    def __init__(self): 
        self._storage: Dict[str, PaymentBase] = {}
        self._channel_index: Dict[str, List[str]] = {}
    def save(self, payment: PaymentBase) -> PaymentBase:
        if not isinstance(payment, PaymentBase):
            raise TypeError("Sadece PaymentBase türevi nesneler kaydedilebilir.")

        self._storage[payment.payment_id] = payment
        
        if payment.channel_id not in self._channel_index:
            self._channel_index[payment.channel_id] = []
        
        if payment.payment_id not in self._channel_index[payment.channel_id]:
            self._channel_index[payment.channel_id].append(payment.payment_id)
            
        print(f"[DB LOG] Kayıt başarılı: {payment.payment_id}")
        return payment

    def find_by_id(self, payment_id: str) -> Optional[PaymentBase]:
        return self._storage.get(payment_id)

    def find_all_by_channel(self, channel_id: str) -> List[PaymentBase]:
        payment_ids = self._channel_index.get(channel_id, [])
        return [self._storage[pid] for pid in payment_ids]

    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[PaymentBase]:
        results = []
        for payment in self._storage.values():
            if start_date <= payment._created_at <= end_date:
                results.append(payment)
        return results

    def filter_by_type(self, payment_type_class) -> List[PaymentBase]:
        return [
            p for p in self._storage.values() 
            if isinstance(p, payment_type_class)
        ]

    def delete(self, payment_id: str) -> bool:
        if payment_id in self._storage:
            payment = self._storage[payment_id]
            if payment.channel_id in self._channel_index:
                if payment_id in self._channel_index[payment.channel_id]:
                    self._channel_index[payment.channel_id].remove(payment_id)
            
            del self._storage[payment_id]
            return True
        return False
    
    @classmethod
    def get_db_info(cls):
        return
    
    @staticmethod
    def validate_currency_code(code: str) -> bool:
        valid_codes = ["TRY", "USD", "EUR", "GBP"]
        return code.upper() in valid_codes