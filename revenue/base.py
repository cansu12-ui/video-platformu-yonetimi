from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Any, Dict
import uuid
import re
import json

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
        
        self._channel_id = self._validate_channel_format(channel_id)
        self._amount = self._validate_amount_initial(amount)
        self._currency = self._validate_currency_code(currency)
        self._period = self._validate_period_regex(period)
        self._status = status
        
        self._logs: List[str] = []
        self._metadata: Dict[str, Any] = {}
        self._priority_level: int = self._calculate_initial_priority()
        
        self.add_log(f"Ödeme başlatıldı. ID: {self._payment_id}")
        self.add_log(f"İlk Tutar: {amount} {currency}")


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
        if not isinstance(value, (int, float)):
            raise TypeError("Tutar sayısal bir değer olmalıdır.")
        if value < 0:
            raise ValueError("Tutar negatif olamaz.")
        
        if value > 50000:
            self.add_log(f"Yüksek tutar uyarısı: {value}")
            self._priority_level = 1
            
        self._amount = float(value)
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
        valid_statuses = [
            "pending", "processing", "completed", 
            "failed", "on_hold", "cancelled", "refunded"
        ]
        if new_status not in valid_statuses:
            raise ValueError(f"Geçersiz durum: {new_status}")
        
        self._status = new_status
        self._updated_at = datetime.now()
        self.add_log(f"Durum değişti: {new_status}")

    def _calculate_initial_priority(self) -> int:
        if self._amount > 100000:
            return 1  # Çok Yüksek Öncelik
        elif self._amount > 10000:
            return 2  # Yüksek Öncelik
        elif self._amount > 1000:
            return 3  # Orta Öncelik
        return 4      # Standart Öncelik

    def _validate_channel_format(self, c_id: str) -> str:
        if not c_id or len(c_id.strip()) < 3:
            raise ValueError("Kanal ID en az 3 karakter olmalıdır.")
        return c_id.strip()

    def _validate_amount_initial(self, val: float) -> float:
        if val < 0:
            raise ValueError("Başlangıç tutarı negatif olamaz.")
        return float(val)

    def _validate_currency_code(self, code: str) -> str:
        if len(code) != 3:
            self.add_log(f"Hatalı kur kodu uzunluğu düzeltildi: {code}")
            return code[:3].upper() if code else "TRY"
        return code.upper()

    def _validate_period_regex(self, p_str: str) -> str:
        pattern = r"^\d{4}-(0[1-9]|1[0-2])$"
        if not re.match(pattern, p_str):
            current_period = datetime.now().strftime("%Y-%m")
            self.add_log(f"Geçersiz dönem formatı ({p_str}). {current_period} atandı.")
            return current_period
        return p_str

    def add_log(self, message: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._logs.append(f"[{ts}] {message}")

    def get_logs(self) -> List[str]:
        return self._logs

    def to_json(self) -> str:
        data = {
            "id": self._payment_id,
            "channel": self._channel_id,
            "amount": self._amount,
            "currency": self._currency,
            "status": self._status,
            "priority": self._priority_level,
            "created_at": self._created_at.isoformat()
        }
        return json.dumps(data, ensure_ascii=False)

    def is_payable(self) -> bool:
        return self._status in ["pending", "on_hold"] and self._amount > 0

    @abstractmethod
    def calculate_tax(self) -> float:
        pass

    @abstractmethod
    def get_payment_details(self) -> dict:
        pass

    def __str__(self):
        return f"Payment<{self.payment_id}> [{self.status}] {self.amount} {self.currency}"