import time
import random
from datetime import datetime, timedelta
from .base import PaymentBase
from .implementations import AdRevenuePayment, MembershipRevenuePayment, SponsorshipPayment
from .repository import InMemoryPaymentRepository
from .services import RevenueService, AnalyticsService

def print_header(title):
    print("\n" + "="*60)
    print(f"{title.center(60)}")
    print("="*60 + "\n")

def create_dummy_data(service: RevenueService, count: int = 50):
    print(f"{count} Adet Rastgele Veri Üretiliyor")
    
    channels = ["UlasDemir", "PythonDersleri", "OyunGemisi", "MuzikKutusu", "VlogTr"]
    currencies = ["TRY", "USD", "EUR"]
    periods = ["2025-01", "2025-02", "2025-03"]
    
    for _ in range(count):
        p_type = random.choice(["ad", "member", "sponsor"])
        channel = random.choice(channels)
        period = random.choice(periods)
        currency = "TRY" 
        
        payment = None
        
        if p_type == "ad":
            impressions = random.randint(1000, 500000)
            cpm = random.uniform(5.0, 25.0)
            amount = (impressions / 1000) * cpm
            payment = AdRevenuePayment(
                channel_id=channel,
                amount=amount,
                currency=currency,
                period=period,
                ad_impressions=impressions,
                cpm_rate=cpm
            )
            
        elif p_type == "member":
            subscribers = random.randint(10, 5000)
            amount = subscribers * 15.0 
            payment = MembershipRevenuePayment(
                channel_id=channel,
                amount=amount,
                currency=currency,
                period=period,
                total_subscribers=subscribers,
                tier_breakdown={"Gold": int(subscribers*0.1), "Silver": int(subscribers*0.9)}
            )
            
        elif p_type == "sponsor":
            amount = random.uniform(5000, 100000)
            payment = SponsorshipPayment(
                channel_id=channel,
                amount=amount,
                currency=currency,
                period=period,
                sponsor_name=f"Sponsor_{random.randint(1,20)}",
                contract_id=f"CNT-{random.randint(1000,9999)}"
            )
        service.create_payment_record(payment)
        
        if random.random() > 0.7:
            service.simulate_payment_processing(payment.payment_id)

    print(" Veri Üretimi Tamamlandı ")

def demo_scenario():
    repo = InMemoryPaymentRepository()
    revenue_service = RevenueService(repo)
    analytics_service = AnalyticsService()
    
    print_header("VIDEO PLATFORMU - GELİR YÖNETİM SİSTEMİ")

    
    create_dummy_data(revenue_service, count=30)


    print_header("TEST 1: Manuel Ödeme Oluşturma ve Polimorfizm")
    
    ad_pay = AdRevenuePayment("KodlayanAdam", 1500.0, "TRY", "2025-04", 100000, 15.0)
    res1 = revenue_service.create_payment_record(ad_pay)
    print(f"Reklam Ödemesi Kayıt: {res1.message}")
    
    sponsor_pay = SponsorshipPayment("KodlayanAdam", 50000.0, "TRY", "2025-04", "TechCorp", "C-99")
    res2 = revenue_service.create_payment_record(sponsor_pay)
    print(f"Sponsor Ödemesi Kayıt: {res2.message}")

    print("\n--- Polimorfizm Gösterimi (Vergi Hesaplama) ---")
    payments_to_calc = [ad_pay, sponsor_pay]
    for p in payments_to_calc:
        print(f"Tür: {type(p).__name__}, Tutar: {p.amount}, Vergi: {p.calculate_tax():.2f}")
        
    print_header("TEST 2: İş Kuralları ve Durum Yönetimi")
    
    low_pay = SponsorshipPayment("YeniKanal", 50.0, "TRY", "2025-04", "MiniMarket", "C-01")
    revenue_service.create_payment_record(low_pay)
    print(f"Düşük Bakiye Ödemesi Eklendi (50 TL). Durum: {low_pay.status}")
    
    print(" 'hold_low_payments' servisi çalıştırılıyor.")
    revenue_service.hold_low_payments(threshold=100.0)
    print(f"İşlem Sonrası Durum: {low_pay.status}")
    
    print("Ödeme Simülasyonu (Banka Entegrasyonu)...")
    sim_res = revenue_service.simulate_payment_processing(sponsor_pay.payment_id)
    print(f"Sponsor Ödemesi Sonuç: {sim_res.message}, Yeni Durum: {sponsor_pay.status}")

    print_header("TEST 3: Raporlama ve Analiz")
    
    report_mar = revenue_service.generate_periodic_report("KodlayanAdam", "2025-03") 
    report_apr = revenue_service.generate_periodic_report("KodlayanAdam", "2025-04") 

    print(f"Kanal: KodlayanAdam - Dönem: 2025-04 Raporu:")
    print(f"Toplam Gelir: {report_apr['total_gross_income']} TL")
    print(f"Tahmini Vergi: {report_apr['total_estimated_tax']} TL")
    print(f"Gelir Dağılımı: {report_apr['breakdown']}")
    
    print(" Dönemsel Karşılaştırma (AnalyticsService):")
    comparison = analytics_service.compare_periods(report_mar, report_apr)
    print(comparison)

    
    print_header("TEST 4: Repository Filtreleme")
    all_sponsors = repo.filter_by_type(SponsorshipPayment)
    print(f"Sistemdeki Toplam Sponsorluk Anlaşması Sayısı: {len(all_sponsors)}")
    
    print("[Demo senaryosu tamamlandı.")

if __name__ == "__main__":
    demo_scenario()