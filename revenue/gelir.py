from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from .base import PaymentBase
@dataclass
class TaxInfo:
    tax_rate: float
    tax_amount: float
    net_amount: float
    country_code: str = "TR"

@dataclass
class PaymentProcessResult:
    success: bool
    transaction_id: str
    message: str
    processed_at: datetime = field(default_factory=datetime.now)

class AdRevenuePayment(PaymentBase):
    def __init__(
        self, 
        channel_id: str, 
        amount: float, 
        currency: str, 
        period: str,
        ad_impressions: int,  
        cpm_rate: float,      
        ad_platform: str = "Google AdSense"
    ):
        super().__init__(channel_id, amount, currency, period) 
        self.ad_impressions = ad_impressions
        self.cpm_rate = cpm_rate
        self.ad_platform = ad_platform
        self._tax_rate = 0.18 

    def calculate_tax(self) -> float:
        tax = self.amount * self._tax_rate
        self.add_log(f"Vergi hesaplandı (Oran: {self._tax_rate}): {tax}")
        return tax

    def get_payment_details(self) -> dict:
        return {
            "type": "AdRevenue",
            "id": self.payment_id,
            "channel": self.channel_id,
            "gross_amount": self.amount,
            "net_amount": self.amount - self.calculate_tax(),
            "currency": self.currency,
            "details": {
                "impressions": self.ad_impressions,
                "cpm": self.cpm_rate,
                "platform": self.ad_platform
            },
            "status": self.status
        }
    
    def update_impressions(self, new_count: int):
        self.ad_impressions = new_count
        new_amount = (self.ad_impressions / 1000) * self.cpm_rate
        self.amount = new_amount
        self.add_log(f"Gösterim güncellendi: {new_count}. Yeni tutar: {self.amount}")