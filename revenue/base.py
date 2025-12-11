

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Any
import uuid

class PaymentBase(ABC):
    

    def __init__(
        self, 
        channel_id: str, 
        amount: float, 
        currency: str, 
        period: str, 
        status: str = "pending"
    ):
        
        self._payment_id: str = str(uuid.uuid4())
        self._created_at: datetime = datetime.now()
        self._updated_at: datetime = datetime.now()
        
        
        self._channel_id = channel_id
        self._amount = amount
        self._currency = currency
        self._period = period
        self._status = status
        
        
        self._logs: List[str] = []
        self.add_log(f"Ödeme nesnesi oluşturuldu. ID: {self._payment_id}, Tutar: {amount} {currency}")

    

    @property
    def payment_id(self) -> str:
        return self._payment_id

    @property
    def channel_id(self) -> str:
        return self._channel_id

    @property
    def amount(self) -> float:
        return self._amount
    
    @amount.setter
    def amount(self, value: float):
        if value < 0:
            raise ValueError("Tutar negatif olamaz.")
        self._amount = value
        self._updated_at = datetime.now()

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def period(self) -> str:
        return self._period

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, new_status: str):
        valid_statuses = ["pending", "processing", "completed", "failed", "on_hold", "cancelled"]
        if new_status not in valid_statuses:
            raise ValueError(f"Geçersiz durum: {new_status}. Beklenenler: {valid_statuses}")
        self._status = new_status
        self._updated_at = datetime.now()
        self.add_log(f"Durum güncellendi: {new_status}")

    @abstractmethod
    def calculate_tax(self) -> float:
        pass

    @abstractmethod
    def get_payment_details(self) -> dict:
        pass
    
    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._logs.append(f"[{timestamp}] {message}")

    def get_logs(self) -> List[str]:
        return self._logs

    def is_payable(self) -> bool:
        return self._status in ["pending", "on_hold"] and self._amount > 0

    def __str__(self):
        return f"Payment(ID={self.payment_id}, Channel={self.channel_id}, Amount={self.amount} {self.currency}, Status={self.status})"