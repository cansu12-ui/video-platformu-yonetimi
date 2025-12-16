from typing import List, Dict
from datetime import datetime
import random
from .base import PaymentBase
from .repository import InMemoryPaymentRepository
from .implementations import PaymentProcessResult, AdRevenuePayment, MembershipRevenuePayment, SponsorshipPayment

class RevenueService:

    def __init__(self, repository: InMemoryPaymentRepository): # DÜZELTME: __init__
        self.repo = repository

    def create_payment_record(self, payment: PaymentBase) -> PaymentProcessResult:
    
        if payment.amount <= 0:
            return PaymentProcessResult(
                success=False, 
                transaction_id="", 
                message="Tutar sıfır veya negatif olamaz."
            )
        if not self.repo.validate_currency_code(payment.currency):
            return PaymentProcessResult(
                success=False, 
                transaction_id="", 
                message=f"Geçersiz para birimi: {payment.currency}"
            )

        self.repo.save(payment)
        return PaymentProcessResult(
            success=True, 
            transaction_id=payment.payment_id, 
            message="Ödeme kaydı başarıyla oluşturuldu."
        )

    def simulate_payment_processing(self, payment_id: str) -> PaymentProcessResult:
        payment = self.repo.find_by_id(payment_id)
        if not payment:
            return PaymentProcessResult(False, "", "Ödeme bulunamadı.")

        if payment.status == "completed":
            return PaymentProcessResult(False, payment_id, "Ödeme zaten tamamlanmış.")

        is_success = random.random() > 0.2

        if is_success:
            payment.status = "completed"
            payment.add_log("Banka onayı alındı. Transfer tamamlandı.")
            return PaymentProcessResult(True, payment_id, "Transfer başarılı.")
        else:
            payment.status = "failed"
            payment.add_log("Banka reddi: Yetersiz bakiye veya teknik hata.")
            return PaymentProcessResult(False, payment_id, "Transfer başarısız.")

    def generate_periodic_report(self, channel_id: str, period: str) -> Dict:
        all_payments = self.repo.find_all_by_channel(channel_id)
        
        period_payments = [p for p in all_payments if p.period == period]
        
        total_gross = sum(p.amount for p in period_payments)
        total_tax = sum(p.calculate_tax() for p in period_payments)
        
        breakdown = {"AdRevenue": 0, "Membership": 0, "Sponsorship": 0}
        
        for p in period_payments:
            if isinstance(p, AdRevenuePayment):
                breakdown["AdRevenue"] += p.amount
            elif isinstance(p, MembershipRevenuePayment):
                breakdown["Membership"] += p.amount
            elif isinstance(p, SponsorshipPayment):
                breakdown["Sponsorship"] += p.amount

        return {
            "channel_id": channel_id,
            "period": period,
            "total_gross_income": total_gross,
            "total_estimated_tax": total_tax,
            "net_income_projection": total_gross - total_tax,
            "breakdown": breakdown,
            "transaction_count": len(period_payments)
        }

    def hold_low_payments(self, threshold: float = 100.0):
        all_payments = self.repo._storage.values()
        
        count = 0
        for payment in all_payments:
            if payment.status == "pending" and payment.amount < threshold:
                payment.status = "on_hold"
                payment.add_log(f"Minimum ödeme eşiği ({threshold}) altında olduğu için beklemeye alındı.")
                count += 1
        
        print(f"[Service Log] {count} adet ödeme beklemeye (on_hold) alındı.")

    def filter_payments_by_status(self, channel_id: str, status: str) -> List[PaymentBase]:
        payments = self.repo.find_all_by_channel(channel_id)
        return [p for p in payments if p.status == status]
    
    def calculate_total_tax_liability(self, payment_list: List[PaymentBase]) -> float:
        total_tax = 0.0
        for payment in payment_list:
            total_tax += payment.calculate_tax()
        return total_tax
    
class AnalyticsService:
    @staticmethod
    def compare_periods(report_old: Dict, report_new: Dict) -> str:
        old_val = report_old.get("total_gross_income", 0)
        new_val = report_new.get("total_gross_income", 0)
        
        if old_val == 0:
            return "Önceki dönem verisi yok."
            
        growth = ((new_val - old_val) / old_val) * 100
        return f"Büyüme Oranı: %{growth:.2f}"