import os
import sys
from datetime import datetime
from typing import Tuple
from .repository import InMemoryPaymentRepository
from .services import RevenueService, AnalyticsService
from .demo import create_dummy_data

def initialize_system() -> Tuple[RevenueService, AnalyticsService]:
    print("-" * 50)
    print("Veritabanı başlatılıyor.")
    repo = InMemoryPaymentRepository()
    
    print("Servis katmanları yükleniyor.")
    revenue_service = RevenueService(repo)
    analytics_service = AnalyticsService()
    
    print("Test verileri sisteme aktarılıyor.")
    create_dummy_data(revenue_service, count=30)
    
    print("Hazır.")
    print("-" * 50)
    return revenue_service, analytics_service

def generate_report_cli(revenue_service: RevenueService):
    print("DÖNEMSEL GELİR RAPORU OLUŞTURUCU")
    print("Örnek Kanallar: UlasDemir, PythonDersleri, KodlayanAdam, OyunGemisi")
    
    channel_id = input("Raporu görmek istediğiniz Kanal ID'sini girin: ").strip()
    
    print("Örnek Dönemler: 2025-01, 2025-02, 2025-03")
    period = input("Dönemi (YYYY-MM) girin: ").strip()

    if not channel_id or not period:
        print("Kanal ID veya Dönem alanı boş bırakılamaz!")
        return

    try:
        report = revenue_service.generate_periodic_report(channel_id, period)
        
        print("\n" + "="*50)
        print(f" GELİR RAPORU: {channel_id}")
        print(f" DÖNEM: {period}")
        print("="*50)
        
        print(f"Toplam İşlem Sayısı  : {report['transaction_count']}")
        currency = report.get('currency', 'TRY') 
        
        print(f"BRÜT GELİR            : {report['total_gross_income']:.2f} {currency}")
        print(f"TAHMİNİ VERGİ YÜKÜ    : {report['total_estimated_tax']:.2f} {currency}")
        print(f"TAHMİNİ NET GELİR     : {report['net_income_projection']:.2f} {currency}")
        
        print("-" * 50)
        print("Gelir Dağılımı:")
        
        has_data = False
        for revenue_type, amount in report['breakdown'].items():
             if amount > 0:
                print(f"  * {revenue_type}: {amount:.2f} {currency}")
                has_data = True

        if not has_data:
             print("Bu dönem için detaylı veri bulunmamaktadır.")
        
        print("="*50)

    except Exception as e:
        print(f"Rapor oluşturulurken teknik bir sorun oluştu: {e}")

def main_menu():
    revenue_service, analytics_service = initialize_system()
    
    while True:
        print("\n" + "*"*45)
        print("   VIDEO PLATFORMU - GELIR YONETIM SISTEMI")
        print("*"*45)
        print("1. Dönemsel Gelir Raporu Görüntüle")
        print("2. Düşük Ödemeleri Askıya Al")
        print("3. Sistem Sağlık Durumu ")
        print("4. En Çok Kazanan İşlemler")
        print("5. Repository Bilgisini Göster")
        print("6. Para Birimi Doğrula")
        print("7. Çıkış")
        print("-" * 45)

        choice = input("işleminizi seçin (1-7): ").strip()

        if choice == '1':
            generate_report_cli(revenue_service)
            
        elif choice == '2':
            try:
                threshold_input = input("Minimum ödeme eşiği: ")
                threshold = float(threshold_input) if threshold_input else 100.0
                print(f" Minimum ödeme eşiği ({threshold} TRY) kontrol ediliyor.")
                count = revenue_service.hold_low_payments(threshold)
                print(f"İs kuralı uygulandı. {count} işlem askıya alındı.")
            except ValueError:
                print("Lütfen geçerli bir sayı girin.")
            
        elif choice == '3':
            print("Sistem Analizi Yapılıyor.")
            health = analytics_service.analyze_system_health(revenue_service.repo)
            print(f"GENEL DURUM: {health['status']}")
            print(f"Hata Oranı : {health['failure_rate']}")
            print(f"Toplam Hacim: {health['total_volume']:.2f}")

        elif choice == '4':
            print("En Yüksek Hacimli işlemler Listeleniyor.")
            tops = analytics_service.get_top_performers(revenue_service.repo, limit=5)
            for t in tops:
                print(f" -> {t}")

        elif choice == '5':
            db_info = revenue_service.repo.get_db_info()
            print(f"[INFO] {db_info}")
            print("Son Sistem Loglari:")
            logs = revenue_service.repo.get_audit_logs(3)
            for log in logs:
                print(f" {log}")
            
        elif choice == '6':
            code = input("Doğrulanacak para birimi (USD, TRY, EUR, GBP ): ").upper()
            is_valid = revenue_service.repo.validate_currency_code(code)
            if is_valid:
                print(f"'{code}' geçerli bir para birimidir.")
            else:
                print(f"'{code}' geçersiz veya desteklenmiyor.")
            
        elif choice == '7':
            print("Sistemden çıkılıyor.")
            break
            
        else:
            print("Geçersiz seçim 1-7 arası rakam girin.")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        sys.exit(0)