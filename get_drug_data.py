import os
import pandas as pd

print("Bakteri verileri ve İlaç Yanıt etiketleri veri tipi korumalı birleştiriliyor...")

try:
    # İndirilenler klasörünün yolunu bul
    user_home = os.path.expanduser("~")
    downloads_dir = os.path.join(user_home, "Downloads")

    bacteria_file = os.path.join(downloads_dir, "data/human_shotgun.rel.full.csv")
    metadata_file = os.path.join(downloads_dir, "data/human_16S.sampleinfo.csv")

    # Lokalde kontrol et
    if not os.path.exists(bacteria_file):
        bacteria_file = "data/human_shotgun.rel.full.csv"
    if not os.path.exists(metadata_file):
        metadata_file = "data/human_16S.sampleinfo.csv"

    # 1. Dosyaları Oku
    df_bacteria = pd.read_csv(bacteria_file, index_col=0)
    df_meta = pd.read_csv(metadata_file)

    # İndeks temizliği (NaN temizleme)
    df_bacteria = df_bacteria[df_bacteria.index.notna()].fillna(0.0)

    # 2. Klinik veriden İlaç Yanıt Sözlüğü Oluştur
    # Doğrudan Python'ın saf tam sayı (int) tipini atıyoruz
    df_meta['label'] = df_meta['Response'].map({'Responder': 1, 'NonResponder': 0})
    label_dict = pd.Series(df_meta.label.values, index=df_meta.Sample).to_dict()

    # 3. Sadece ortak olan hastaları filtrele
    common_samples = [col for col in df_bacteria.columns if col in label_dict]
    df_bacteria_filtered = df_bacteria[common_samples].copy()

    # 4. 'disease' satırını saf int değerleri içeren bir liste olarak oluştur
    disease_row = [int(label_dict[sample]) for sample in common_samples]

    # Matrisin en altına ekle
    df_bacteria_filtered.loc['disease'] = disease_row

    # İndeks adını ayarla
    df_bacteria_filtered.index.name = "Taxa"

    # 5. Kaydetme Formatı Güvenliği
    # Pandas bazen float matrislerin altına int eklenince tüm dosyayı float yazar (.0 ekler).
    # DeepMicro'nun okurken patlamaması için float biçimlendirmesini optimize ediyoruz.
    os.makedirs("data", exist_ok=True)
    output_path = "data/abundance_DrugResponse.txt"

    # Dosyayı kaydederken disease satırının ondalıksız kalmasını sağlamak için manuel düzeltme yerine
    # sekmeli yazma işlemini optimize ediyoruz.
    df_bacteria_filtered.to_csv(output_path, sep='\t', index_label="Taxa")

    # Dosyayı metin olarak okuyup en alt satırdaki "0.0" ve "1.0" ifadelerini kesin olarak "0" ve "1" yapıyoruz.
    with open(output_path, 'r') as f:
        lines = f.readlines()

    if lines[-1].startswith('disease'):
        # disease satırındaki .0 uzantılarını temizle
        lines[-1] = lines[-1].replace('.0\t', '\t').replace('.0\n', '\n')
        if lines[-1].endswith('.0'):
            lines[-1] = lines[-1][:-2]

    with open(output_path, 'w') as f:
        f.writelines(lines)

    print("\n" + "=" * 60)
    print("[KUSURSUZ BAŞARILI] İlaç Yanıtı Veri Seti Tip Hatasından Arındırıldı!")
    print(f"Dosya Konumu: {output_path}")
    print(f"Toplam Eşleşen Hasta Sayısı: {len(common_samples)}")
    print("=" * 60)

except Exception as e:
    print("\n[HATA] Birleştirme yapılırken sorun oluştu:", e)