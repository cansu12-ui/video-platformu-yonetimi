from typing import List, Dict, Optional, Any
from datetime import datetime
import random
from .base import PaymentBase
from .repository import InMemoryPaymentRepository
from .implementations import PaymentProcessResult, AdRevenuePayment, MembershipRevenuePayment, SponsorshipPayment

class RevenueService:

    def __init__(self, repository: InMemoryPaymentRepository):
        self.repo = repository

    def create_payment_record(self, payment: PaymentBase) -> PaymentProcessResult:
        try:
            if not payment.is_payable():
                return PaymentProcessResult(False, "", "Ödeme yapılabilir durumda değil (Tutar 0 veya statü hatalı).")

            if payment.amount <= 0:
                return PaymentProcessResult(False, "", "Tutar sıfır veya negatif olamaz.")
            
            if not self.repo.validate_currency_code(payment.currency):
                return PaymentProcessResult(False, "", f"Geçersiz para birimi: {payment.currency}")

            self.repo.save(payment)
            return PaymentProcessResult(
                success=True, 
                transaction_id=payment.payment_id, 
                message="Ödeme kaydı başarıyla oluşturuldu."
            )

        except ValueError as ve:
            return PaymentProcessResult(False, "", f"Veri Doğrulama Hatası: {str(ve)}")
        except MemoryError as me:
            return PaymentProcessResult(False, "", f"Sistem Hatası: {str(me)}")
        except Exception as e:
            return PaymentProcessResult(False, "", f"Bilinmeyen Hata: {str(e)}")

    def simulate_payment_processing(self, payment_id: str) -> PaymentProcessResult:
        payment = self.repo.find_by_id(payment_id)
        if not payment:
            return PaymentProcessResult(False, "", "Ödeme bulunamadı.")

        if payment.status == "completed":
            return PaymentProcessResult(False, payment_id, "Ödeme zaten tamamlanmış.")

        if payment.amount > 50000 and payment.status != "processing":
            payment.status = "processing"
            payment.add_log("Yüksek tutar nedeniyle işlem manuel incelemeye alındı.")
            return PaymentProcessResult(True, payment_id, "İşlem manuel onay kuyruğuna alındı.")

        is_success = random.random() > 0.15  # %15 Hata payı

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
        
        breakdown = {"AdRevenue": 0.0, "Membership": 0.0, "Sponsorship": 0.0}
        
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
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_gross_income": round(total_gross, 2),
            "total_estimated_tax": round(total_tax, 2),
            "net_income_projection": round(total_gross - total_tax, 2),
            "breakdown": breakdown,
            "transaction_count": len(period_payments)
        }

    def hold_low_payments(self, threshold: float = 100.0):
        low_payments = self.repo.find_by_amount_range(0.01, threshold)
        
        count = 0
        for payment in low_payments:
            if payment.status == "pending":
                payment.status = "on_hold"
                payment.add_log(f"Minimum ödeme eşiği ({threshold}) altında olduğu için beklemeye alındı.")
                count += 1
        
        print(f"[Service Log] {count} adet ödeme beklemeye alındı.")
        return count

    def filter_payments_by_status(self, channel_id: str, status: str) -> List[PaymentBase]:
        channel_payments = self.repo.find_all_by_channel(channel_id)
        return [p for p in channel_payments if p.status == status]
    
    def calculate_total_tax_liability(self, payment_list: List[PaymentBase]) -> float:
        total_tax = 0.0
        for payment in payment_list:
            total_tax += payment.calculate_tax()
        return round(total_tax, 2)
    
    def bulk_status_update(self, payment_ids: List[str], new_status: str) -> int:
        success_count = 0
        for pid in payment_ids:
            payment = self.repo.find_by_id(pid)
            if payment:
                try:
                    payment.status = new_status
                    success_count += 1
                except ValueError:
                    continue 
        return success_count

class AnalyticsService: 
    
    @staticmethod
    def compare_periods(report_old: Dict, report_new: Dict) -> str:
        old_val = report_old.get("total_gross_income", 0)
        new_val = report_new.get("total_gross_income", 0)
        
        if old_val == 0:
            return "Önceki dönem verisi yok."
            
        growth = ((new_val - old_val) / old_val) * 100
        trend_icon = "(+)" if growth > 0 else "(-)"
        return f"Büyüme Oranı: %{growth:.2f} {trend_icon}"

    def analyze_system_health(self, repository: InMemoryPaymentRepository) -> Dict[str, Any]:
        status_dist = repository.get_status_distribution()
        total_vol = repository.get_total_volume()
        audit_logs = repository.get_audit_logs(limit=5)
        
        failed = status_dist.get("failed", 0)
        total_ops = sum(status_dist.values())
        failure_rate = (failed / total_ops * 100) if total_ops > 0 else 0
        
        return {
            "status": "Healthy" if failure_rate < 5 else "Warning",
            "total_volume": total_vol,
            "transaction_counts": status_dist,
            "failure_rate": f"%{failure_rate:.2f}",
            "recent_logs": audit_logs
        }
        
    def get_top_performers(self, repository: InMemoryPaymentRepository, limit: int = 5) -> List[str]:
        top_payments = repository.get_top_payments(limit)
        results = []
        for p in top_payments:
            results.append(f"{p.channel_id}: {p.amount} {p.currency} ({p.__class__.__name__})")
        return results