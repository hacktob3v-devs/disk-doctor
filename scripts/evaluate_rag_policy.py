"""
Policy-level retrieval check on colloquial Turkish customer messages.

scripts/evaluate_honest_metrics.py scores a hit when the retrieved policy has the
right *category*; this script requires the exact policy, which is what the reply
is grounded on.

Usage: python scripts/evaluate_rag_policy.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.rag_engine import get_rag_engine, retrieve_policies  # noqa: E402

CASES = [
 ("Çantayı iade etmek istiyorum, nasıl yapabilirim?", "POL_IADE_01"),
 ("14 gün dolmadan cayma hakkımı kullanmak istiyorum", "POL_IADE_01"),
 ("Kartımdan iki kere çekildi", "POL_TEKNIK_01"),
 ("Ödeme sırasında sayfa dondu, iki kez para çekildi", "POL_TEKNIK_01"),
 ("Kargom 5 gündür gelmedi, nerede?", "POL_KARGO_01"),
 ("Siparişim aktarma merkezinde bekliyor hareket yok", "POL_KARGO_01"),
 ("Kutu ezik geldi içindeki kupa kırılmış", "POL_KARGO_02"),
 ("Kurye adreste kimse yok demiş, paket şubede", "POL_KARGO_03"),
 ("Dikişi söküldü, değişim mümkün mü?", "POL_URUN_01"),
 ("Ayakkabının tabanı ikinci gün ayrıldı", "POL_URUN_01"),
 ("Pantolon dar geldi 42 beden ile değiştirebilir miyim", "POL_URUN_03"),
 ("İadem ne zaman hesabıma geçer?", "POL_IADE_05"),
 ("İade ettim ama param kartıma yansımadı", "POL_IADE_05"),
 ("Bir kere kullandım etiketini kestim iade etmek istiyorum", "POL_IADE_03"),
 ("İç çamaşırının paketini açtım iade edebilir miyim", "POL_IADE_02"),
 ("İade kodu nedir hangi kargo ile göndermeliyim", "POL_IADE_04"),
 ("SMS doğrulama kodu gelmiyor giriş yapamıyorum", "POL_TEKNIK_02"),
 ("İndirim kuponum sepette çalışmıyor", "POL_TEKNIK_03"),
 ("Hafta sonu açık mısınız, telefonla ulaşamıyorum", "POL_GENEL_01"),
 ("Ürün harika, çok teşekkürler", "POL_GENEL_02"),
 ("Cihaz arızalandı garanti kapsamında mı", "POL_URUN_02"),
]


def main() -> None:
    engine = get_rag_engine()
    reranker = "on" if engine.reranker_model is not None else "off (keyword/semantic only)"
    misses = []
    for text, expected in CASES:
        got = retrieve_policies(text, top_k=3)["best_policy_id"]
        if got != expected:
            misses.append((text, expected, got))
    hits = len(CASES) - len(misses)
    print(f"Cross-Encoder: {reranker}")
    print(f"Policy Hit@1: {hits}/{len(CASES)} (%{hits / len(CASES) * 100:.1f})")
    for text, expected, got in misses:
        print(f"  MISS  {expected} -> {got}  | {text}")


if __name__ == "__main__":
    main()
