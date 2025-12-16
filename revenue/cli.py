from .repository import InMemoryPaymentRepository
from .services import RevenueService, AnalyticsService
from .demo import create_dummy_data 
from datetime import datetime
import json
import os

def initialize_system():
    repo = InMemoryPaymentRepository()
    revenue_service = RevenueService(repo)
    analytics_service = AnalyticsService()
    
    print("Sistem Başlatılıyor: Temel Veri Kümesi Oluşturuluyor.")
    create_dummy_data(revenue_service, count=30)
    return revenue_service, analytics_service

def generate_report_cli(revenue_service: RevenueService):
    print("Dönemsel Gelir Raporu Oluşturucu")
    
    print("Örnek Kanallar: UlasDemir, PythonDersleri, KodlayanAdam")
    channel_id = input("Raporu görmek istediğiniz Kanal ID'sini girin: ").strip()
    
    print("Örnek Dönemler: 2025-01, 2025-02, 2025-03, 2025-04")
    period = input("Dönemi (örn: YYYY-MM) girin: ").strip()

    if not channel_id or not period:
        print("Kanal ID veya Dönem boş bırakılamaz.")
        return

    try:
        report = revenue_service.generate_periodic_report(channel_id, period)
        
        print("\n" + "="*50)
        print(f"💰 {channel_id} Kanalı - {period} Dönemi Gelir Raporu")
        print("="*50)
        print(f"Toplam İşlem Sayısı: {report['transaction_count']}")
        
        currency = "TRY" 
        print(f"BRÜT GELİR: {report['total_gross_income']:.2f} {currency}")
        print(f"TAHMİNİ VERGİ YÜKÜ: {report['total_estimated_tax']:.2f} {currency}")
        print(f"TAHMİNİ NET GELİR: {report['net_income_projection']:.2f} {currency}")
        print("-" * 50)
        print("Gelir Dağılımı (Türlere Göre):")
        
        has_data = False
        for revenue_type, amount in report['breakdown'].items():
             if amount > 0:
                print(f"  * {revenue_type.ljust(15)}: {amount:.2f} {currency}")
                has_data = True

        if not has_data and report['transaction_count'] > 0:
             pass 
        elif report['transaction_count'] == 0:
             print("Bu dönem için kayıt bulunamadı.")
        
        print("="*50)

    except Exception as e:
        print(f"Rapor oluşturulurken bir hata oluştu: {e}")