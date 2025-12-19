from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Union
import random
import uuid
from .base import PaymentBase

@dataclass
class VergiBilgisi:
    matrah: float
    vergi_orani: float
    vergi_tutari: float
    net_odenecek: float
    para_birimi: str
    hesaplama_tarihi: datetime = field(default_factory=datetime.now)

@dataclass
class ReklamPerformansMetriki:
    toplam_gosterim: int
    gecerli_gosterim: int
    tahmini_tiklama: int
    ortalama_cpm: float
    platform: str

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
        self.ad_impressions =ad_impressions
        self.cpm_rate = cpm_rate
        self.ad_platform = ad_platform
        self._vergi_orani = 0.18 
        self._gecersiz_trafik_orani = 0.02 
        self._bonus_esigi = 1000000
        self._performans_bonusu = 0.05
        self._metrik_onbellek = self._metrikleri_olustur()

    def _gosterim_dogrula(self, deger: int) -> int:
        if not isinstance(deger, int):
            try:
                deger = int(deger)
            except:
                raise TypeError("Gösterim sayısı tam sayı olmalıdır.")
        if deger < 0:
            raise ValueError("Gösterim sayısı negatif olamaz.")
        return deger

    def _cpm_dogrula(self, deger: float) -> float:
        if deger < 0.0:
            raise ValueError("CPM oranı sıfırdan küçük olamaz.")
        if deger > 1000.0:
            self.add_log(f"Uyarı: Anormal yüksek CPM oranı tespit edildi: {deger}")
        return float(deger)

    def _platform_kontrol(self, isim: str) -> str:
        gecerli_platformlar = ["Google AdSense", "Facebook Ads", "Unity Ads", "TikTok Business", "YouTube Partner"]
        if isim not in gecerli_platformlar:
            self.add_log(f"Bilinmeyen platform '{isim}'. Varsayılan olarak AdSense atandı.")
            return "Google AdSense"
        return isim

    def _metrikleri_olustur(self) -> ReklamPerformansMetriki:
        tiklama_orani = 0.015 
        return ReklamPerformansMetriki(
            toplam_gosterim=self.ad_impressions,
            gecerli_gosterim=int(self.ad_impressions * (1 - self._gecersiz_trafik_orani)),
            tahmini_tiklama=int(self.ad_impressions * tiklama_orani),
            ortalama_cpm=self.cpm_rate,
            platform=self.ad_platform
        )

    def calculate_tax(self) -> float:
        duzeltilmis_gelir = self.net_kazanc_hesapla()
        vergi = duzeltilmis_gelir * self._vergi_orani
        self.add_log(f"Vergi matrahı: {duzeltilmis_gelir}, Hesaplanan vergi: {vergi}")
        return round(vergi, 2)

    def net_kazanc_hesapla(self) -> float:
        ham_kazanc = (self.ad_impressions / 1000) * self.cpm_rate
        kesinti = ham_kazanc * self._gecersiz_trafik_orani
        bonus = 0.0
        
        if self.ad_impressions > self._bonus_esigi:
            bonus = ham_kazanc * self._performans_bonusu
            
        sonuc = ham_kazanc - kesinti + bonus
        return round(sonuc, 2)

    def get_payment_details(self) -> dict:
        kazanc = self.net_kazanc_hesapla()
        vergi = self.calculate_tax()
        
        return {
            "type": "AdRevenue",
            "id": self.payment_id,
            "channel": self.channel_id,
            "financial_data": {
                "gross_input": self.amount,
                "adjusted_earnings": kazanc,
                "tax_amount": vergi,
                "net_payout": kazanc - vergi,
                "currency": self.currency
            },
            "ad_metrics": {
                "total_impressions": self.ad_impressions,
                "valid_impressions": self._metrik_onbellek.gecerli_gosterim,
                "estimated_clicks": self._metrik_onbellek.tahmini_tiklama,
                "cpm": self.cpm_rate,
                "platform": self.ad_platform,
                "bonus_applied": self.ad_impressions > self._bonus_esigi
            },
            "status": self.status
        }
    
    def update_impressions(self, new_count: int):
        eski_deger = self.ad_impressions
        self.ad_impressions = self._gosterim_dogrula(new_count)
        yeni_tutar = self.net_kazanc_hesapla()
        self.amount = yeni_tutar
        self._metrik_onbellek = self._metrikleri_olustur()
        self.add_log(f"Gösterim güncellendi: {eski_deger} -> {new_count}. Yeni hakediş: {self.amount}")

    def sahtecilik_kontrolu_yap(self) -> bool:
        risk_skoru = random.random()
        if risk_skoru > 0.98:
            self.status = "on_hold"
            self.add_log("Yüksek riskli trafik tespit edildi. Ödeme askıya alındı.")
            return False
        return True


class MembershipRevenuePayment(PaymentBase):
    def __init__(
        self, 
        channel_id: str, 
        amount: float, 
        currency: str, 
        period: str,
        total_subscribers: int,
        tier_breakdown: Dict[str, int]  
    ):
        super().__init__(channel_id, amount, currency, period) 
        
        self.total_subscribers = self._abone_sayisi_dogrula(total_subscribers)
        self.tier_breakdown = self._tier_dagilimi_dogrula(tier_breakdown)
        self._platform_fee_rate = 0.30 
        self._iade_rezerv_orani = 0.05 
        self._stopaj_orani = 0.20 

    def _abone_sayisi_dogrula(self, sayi: int) -> int:
        if sayi < 0:
            raise ValueError("Abone sayısı negatif olamaz.")
        return sayi

    def _tier_dagilimi_dogrula(self, dagilim: Dict[str, int]) -> Dict[str, int]:
        toplam = sum(dagilim.values())
        if toplam != self.total_subscribers:
            fark = self.total_subscribers - toplam
            if fark > 0:
                dagilim["Diger"] = dagilim.get("Diger", 0) + fark
            elif fark < 0:
                self.add_log("Uyarı: Tier dağılımı toplam abone sayısından fazla. Veri tutarsızlığı.")
        return dagilim

    def calculate_tax(self) -> float:
        net_after_fee = self.amount * (1 - self._platform_fee_rate)
        vergi_matrahi = net_after_fee * (1 - self._iade_rezerv_orani)
        vergi = vergi_matrahi * self._stopaj_orani
        
        self.add_log(f"Platform (%30) ve Stopaj (%20) hesaplandı: {vergi}")
        return round(vergi, 2)

    def calculate_platform_share(self) -> float:
        return round(self.amount * self._platform_fee_rate, 2)

    def arpu_hesapla(self) -> float:
        if self.total_subscribers <= 0:
            return 0.0
        return round(self.amount / self.total_subscribers, 2)

    def get_payment_details(self) -> dict:
        return {
            "type": "MembershipRevenue",
            "id": self.payment_id,
            "revenue_breakdown": {
                "gross_amount": self.amount,
                "platform_fee": self.calculate_platform_share(),
                "refund_reserve": self.amount * self._iade_rezerv_orani,
                "tax": self.calculate_tax()
            },
            "subscriber_stats": {
                "total_count": self.total_subscribers,
                "arpu": self.arpu_hesapla(),
                "active_tiers": list(self.tier_breakdown.keys())
            },
            "tiers": self.tier_breakdown,
            "status": self.status
        }
    
    def gelecek_ay_tahmini_yap(self, churn_rate: float = 0.05) -> float:
        kalan_aboneler = self.total_subscribers * (1 - churn_rate)
        mevcut_arpu = self.arpu_hesapla()
        tahmin = kalan_aboneler * mevcut_arpu
        self.add_log(f"Gelecek ay tahmini yapıldı (Churn: %{churn_rate*100}): {tahmin}")
        return round(tahmin, 2)


class SponsorshipPayment(PaymentBase):
    def __init__( 
        self, 
        channel_id: str, 
        amount: float, 
        currency: str, 
        period: str,
        sponsor_name: str,
        contract_id: str
    ):
        super().__init__(channel_id, amount, currency, period) 
        
        self.sponsor_name = self._isim_kontrol(sponsor_name)
        self.contract_id = self._sozlesme_no_kontrol(contract_id)
        
        self.is_invoice_sent = False
        self.taksit_sayisi = 1
        self.teslimat_onaylandi = False

    def _isim_kontrol(self, isim: str) -> str:
        if not isim or len(isim.strip()) < 2:
            return "Bilinmeyen Sponsor"
        return isim.strip()

    def _sozlesme_no_kontrol(self, c_id: str) -> str:
        if not c_id.startswith("CNT-") and not c_id.startswith("SP-"):
            yeni_id = f"CNT-{uuid.uuid4().hex[:6].upper()}"
            self.add_log(f"Hatalı sözleşme no ({c_id}). Otomatik atandı: {yeni_id}")
            return yeni_id
        return c_id

    def calculate_tax(self) -> float:
        kurumlar_vergisi = 0.20
        damga_vergisi = 0.00948 
        toplam_oran = kurumlar_vergisi + damga_vergisi
        return round(self.amount * toplam_oran, 2)

    def get_payment_details(self) -> dict:
        return {
            "type": "Sponsorship",
            "id": self.payment_id,
            "contract_info": {
                "sponsor": self.sponsor_name,
                "contract_id": self.contract_id,
                "deliverables_status": "Onaylandı" if self.teslimat_onaylandi else "Beklemede"
            },
            "payment_info": {
                "total_amount": self.amount,
                "installments_count": self.taksit_sayisi,
                "amount_per_installment": self.taksit_tutari_hesapla(),
                "invoice_sent": self.is_invoice_sent,
                "tax": self.calculate_tax()
            },
            "status": self.status
        }
    
    def mark_invoice_sent(self):
        if self.is_invoice_sent:
            self.add_log("Fatura zaten gönderilmiş.")
            return
        self.is_invoice_sent = True
        fatura_no = f"INV-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
        self.add_log(f"Fatura kesildi ve sponsora ({self.sponsor_name}) gönderildi. No: {fatura_no}")

    def taksit_plani_olustur(self, taksit_adedi: int):
        if taksit_adedi < 1:
            raise ValueError("Taksit sayısı en az 1 olmalıdır.")
        self.taksit_sayisi = taksit_adedi
        self.add_log(f"Ödeme planı {taksit_adedi} taksit olarak güncellendi.")

    def taksit_tutari_hesapla(self) -> float:
        return round(self.amount / self.taksit_sayisi, 2)

    def teslimat_onayla(self):
        self.teslimat_onaylandi = True
        self.add_log("Sponsorluk gereksinimleri (video/içerik) tamamlandı olarak işaretlendi.")

    def __repr__(self):
        return f"<Sponsorluk: {self.sponsor_name} -> {self.channel_id} | {self.amount} {self.currency}>"