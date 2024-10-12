import os
import json
import asyncio
import revolt
import aiohttp
from typing import Union
from revolt.ext import commands
import time

def load_json_data(dosya_adi):
    if os.path.exists(dosya_adi):
        with open(dosya_adi, 'r') as f:
            return json.load(f) # neden json kaydetme yöntemi kullandım?: ü ş e n d i m
    return {}

def save_json_data(dosya_adi, veri):
    with open(dosya_adi, 'w') as f:
        json.dump(veri, f, indent=4)  # gizlilik nedeni ile bunlar github'da yok bu arada verileri.

# Şimdi soracaksınız, neden commands ekleyipte kullanmıyorsun?
# VDS'de commands tam çalışmadı, revolt.Client'ın kendiside çalışmadı. Yani 2 taraflık bir kütüphane sorunu var ama çokta kafaya takmayın.



class Client(commands.CommandsClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baslangic_zamani = time.monotonic()

    async def get_prefix(self, mesaj: revolt.Message):
        return "s!" # ne olur ne olmaz diye

    async def on_ready(self):
        sunucular = self.servers 
        sunucu_sayisi = len(sunucular)
        await self.edit_status(presence=revolt.PresenceType.online, text=f"{sunucu_sayisi} sunucuda")
        print(f"Revolt botu {sunucu_sayisi} sunucuda çalışıyor.")
        
    async def on_member_join(self, uye: revolt.Member):
        sunucu_id = str(uye.server.id)
        veritabanı = load_json_data('veritabani.json')
        otorol_verisi = veritabanı.get('otorol', {})
        
        if sunucu_id in otorol_verisi:
            rol_id = otorol_verisi[sunucu_id]
            rol = uye.server.get_role(rol_id)
            if rol:
                await uye.edit(roles=uye.roles + [rol])
                print(f"{uye.name} kullanıcısına otorol ({rol.name}) verildi.")

    async def send_message_to_channel(self, kanal_id: str, icerik: str):
        kanal = await Client.fetch_channel(self, kanal_id)
        await kanal.send(icerik)

    async def on_message(self, mesaj: revolt.Message):
        if mesaj.author.id == self.user.id:
            return
        
        kullanici_id = mesaj.author.id
        mevcut_zaman = mesaj.created_at.timestamp()

        if mesaj.content.startswith("s!ping"):
            baslangic_zamani = time.monotonic()
            msg = await mesaj.channel.send("***Pingleniyor..***")
            bitis_zamani = time.monotonic()
            ping = round((bitis_zamani - baslangic_zamani) * 1000)
            await msg.edit(content=f"🏓 **Pong!** Gecikme süresi *{ping}*ms")

        elif mesaj.content.startswith("s!kick"):
            try:
                izinler = mesaj.author.get_permissions()
                if izinler.kick_members:
                    args = mesaj.content.split(" ")
                    if len(args) < 2:
                        await mesaj.channel.send("❌ Kullanıcı ID'si girmeniz gerekiyor.")
                        return

                    kullanici_id = args[1]
                    kullanici = mesaj.server.get_member(kullanici_id)
                    if kullanici:
                        author_highest_role = sorted(mesaj.author.roles, key=lambda r: r.rank, reverse=True)
                        target_highest_role = sorted(kullanici.roles, key=lambda r: r.rank, reverse=True)

                        author_rank = author_highest_role[0].rank if author_highest_role else 0
                        target_rank = target_highest_role[0].rank if target_highest_role else 0

                        if target_rank >= author_rank:
                            await mesaj.channel.send("❌ Kendinizden üstteki bir kullanıcıyı atamazsınız.")
                            return
                        await kullanici.kick()
                        await mesaj.channel.send(f"✅ **{kullanici.name}** başarıyla atıldı.")
                    else:
                        await mesaj.channel.send("❌ Kullanıcı bulunamadı.")
                else:
                    await mesaj.channel.send("❌ Bu komutu kullanmak için yeterli yetkiniz yok.")
            except Exception as e:
                await mesaj.channel.send(f"Bir hata oluştu: {e}")

        elif mesaj.content.startswith("s!ban"):
            try:
                izinler = mesaj.author.get_permissions()
                if izinler.ban_members:
                    args = mesaj.content.split(" ")
                    if len(args) < 2:
                        await mesaj.channel.send("❌ Kullanıcı ID'si girmeniz gerekiyor.")
                        return

                    kullanici_id = args[1]
                    kullanici = mesaj.server.get_member(kullanici_id)
                    if kullanici:
                        author_highest_role = sorted(mesaj.author.roles, key=lambda r: r.rank, reverse=True)
                        target_highest_role = sorted(kullanici.roles, key=lambda r: r.rank, reverse=True)

                        author_rank = author_highest_role[0].rank if author_highest_role else 0
                        target_rank = target_highest_role[0].rank if target_highest_role else 0

                        if target_rank >= author_rank:
                            await mesaj.channel.send("❌ Kendinizden üstteki bir kullanıcıyı yasaklayamazsınız.")
                            return
                        await kullanici.ban()
                        await mesaj.channel.send(f"🔨 **{kullanici.name}** başarıyla yasaklandı.")
                    else:
                        await mesaj.channel.send("❌ Kullanıcı bulunamadı.")
                else:
                    await mesaj.channel.send("❌ Bu komutu kullanmak için yeterli yetkiniz yok.")
            except Exception as e:
                await mesaj.channel.send(f"Bir hata oluştu: {e}")


        elif mesaj.content.startswith("s!durum"):
            surum = "1.0.0"
            sunucu_sayisi = len(self.servers)
            toplam_uyeler = sum(len(server.members) for server in self.servers)
            calisma_suresi = time.monotonic() - self.baslangic_zamani
            calisma_saniye = int(calisma_suresi)
            calisma_mesaji = f"{calisma_saniye // 3600} saat, {(calisma_saniye % 3600) // 60} dakika, {calisma_saniye % 60} saniye"

            durum_mesaji = (
                f"🤖 **Bot Durumu:**\n"
                f"📦 **Sürüm:** {surum}\n"
                f"🌐 **Sunucu Sayısı:** {sunucu_sayisi}\n"
                f"👥 **Toplam Üye Sayısı:** {toplam_uyeler}\n"
                f"⏳ **Çalışma Süresi:** {calisma_mesaji}\n"
            )
            await mesaj.channel.send(durum_mesaji)

        elif mesaj.content.startswith("s!help") or mesaj.content == self.user.mention:
            komutlar_listesi = {
                "🔧 **Temel Komutlar:**": [
                    ("ping", "Ping komutu, botun çalıştığını kontrol eder."),
                    ("durum", "Botun durumu hakkında bilgi verir."),
                ],
                "👮 **Yönetim Komutları:**": [
                    ("kick <kullanici id>", "Belirtilen kullanıcıyı sunucudan atar."),
                    ("ban <kullanici id>", "Belirtilen kullanıcıyı sunucudan yasaklar."),
                    ("mute <kullanici id> <saniye>", "Belirtilen kullanıcıyı susturur.  **[HENÜZ REVOLTTA MEVCUT DEĞİLDİR.]**"),
                ],
                "⚙️ **Otomasyon Komutları:**": [
                    ("otorol <rol id>", "Sunucunuza yeni girenlere otomatik rol vermenizi sağlar."),
                    ("herkeserolver <rol id>", "Tüm üyelere belirtilen rolü verir."),
                ],
                "🌐 **Sunucu Bilgisi:**": [
                    ("sunucu", "Sunucu hakkında bilgi verir."),
                ],
            }
            
            yardim_mesaji = "📜 **Komutlar:**\n"
            for kategori, komutlar in komutlar_listesi.items():
                yardim_mesaji += f"{kategori}\n"
                for komut, aciklama in komutlar:
                    yardim_mesaji += f"  - **{komut}**: {aciklama}\n"
                yardim_mesaji += "\n"

            await mesaj.channel.send(yardim_mesaji)

        elif mesaj.content.startswith("s!mute"):
            izinler = mesaj.author.get_permissions()
            if izinler.mute_members: 
                args = mesaj.content.split(" ")
                if len(args) < 3:
                    await mesaj.channel.send("❌ Lütfen kullanıcı ID'sini ve süreyi belirtin. Örnek: `s!mute <kullanici_id> <süre>`")
                    return
                
                kullanici_id = args[1]
                susturma_suresi = int(args[2])
                kullanici = mesaj.server.get_member(kullanici_id)
                if kullanici:
                    await kullanici.timeout(susturma_suresi)
                    await mesaj.channel.send(f"🔇 **{kullanici.name}** başarıyla {susturma_suresi} saniye susturuldu.")
                else:
                    await mesaj.channel.send("❌ Kullanıcı bulunamadı.")
            else:
                await mesaj.channel.send("❌ Bu komutu kullanmak için yeterli yetkiniz yok.")

        elif mesaj.content.startswith("s!otorol"):
            izinler = mesaj.author.get_permissions()
            if izinler.manage_role:
                args = mesaj.content.split(" ")
                if len(args) < 2:
                    await mesaj.channel.send("❌ Lütfen bir rol ID'si belirtin. Örnek: `s!otorol <rol_id>`")
                    return

                rol_id = args[1]
                rol = mesaj.server.get_role(rol_id)
                if rol:
                    veritabanı = load_json_data('veritabani.json')
                    otorol_verisi = veritabanı.get('otorol', {})
                    otorol_verisi[str(mesaj.server.id)] = rol_id
                    veritabanı['otorol'] = otorol_verisi
                    save_json_data('veritabani.json', veritabanı)
                    await mesaj.channel.send(f"✅ Otorol başarıyla {rol.name} olarak ayarlandı.")
                else:
                    await mesaj.channel.send("❌ Belirtilen rol bulunamadı.")
                    
        if mesaj.content.startswith("s!herkeserolver"):
            if mesaj.author.id == mesaj.server.owner.id:
                args = mesaj.content.split(" ")
                if len(args) < 2:
                    await mesaj.channel.send("❌ Lütfen bir rol ID'si belirtin. Örnek: `s!herkeserolver <rol_id>`")
                    return

                rol_id = args[1]
                rol = mesaj.server.get_role(rol_id)
                durum_mesaji = await mesaj.channel.send("Herkese rol veriliyor. Lütfen bekleyiniz..")
                if rol:
                    uyeler = mesaj.server.members
                    toplam_uyeler = len(uyeler)
                    basarili = 0

                    for index, uye in enumerate(uyeler):
                        try:
                            await uye.edit(roles=uye.roles + [rol])
                            basarili += 1
                        except Exception as e:
                            print(f"Rol verilemedi: {uye.name}, Hata: {e}")
                            continue

                        yuzde = int((index + 1) / toplam_uyeler * 100)
                        await durum_mesaji.edit(content=f"İlerleme: %{yuzde} ({index + 1}/{toplam_uyeler}) üye işlendi.")
                        
                        await asyncio.sleep(3)

                    await durum_mesaji.edit(content=f"✅ {basarili}/{toplam_uyeler} üyeye başarıyla {rol.name} rolü verildi!")
                else:
                    await mesaj.channel.send("❌ Belirtilen rol bulunamadı.")
            else:
                await mesaj.channel.send("❌ Bu komutu kullanmak için sunucu sahibi olmalısınız!")

        elif mesaj.content.startswith("s!sunucu"):
            sunucu_adi = mesaj.server.name
            sunucu_sahibi = mesaj.server.owner.name
            uye_sayisi = len(mesaj.server.members)
            çevrimiçi_uyeler = sum(1 for uye in mesaj.server.members if uye.status == revolt.PresenceType.online)
            rol_sayisi = len(mesaj.server.roles)
            olusma_tarihi = mesaj.server.created_at.strftime("%Y-%m-%d %H:%M:%S")

            sunucu_bilgi_mesaji = (
                f"🌐 **Sunucu Bilgileri:**\n"
                f"🏷️ **Sunucu Adı:** {sunucu_adi}\n"
                f"👤 **Sahibi:** {sunucu_sahibi}\n"
                f"👥 **Toplam Üye Sayısı:** {uye_sayisi}\n"
                f"🟢 **Çevrimiçi Üye Sayısı:** {çevrimiçi_uyeler}\n"
                f"🎭 **Rol Sayısı:** {rol_sayisi}\n"
                f"📅 **Oluşturulma Tarihi:** {olusma_tarihi}\n"
            )
            await mesaj.channel.send(sunucu_bilgi_mesaji)

async def start_revolt_bot():
    async with revolt.utils.client_session() as session:
        client = Client(session, os.getenv("REVOLT_TOKEN"))
        print("Revolt Securium Botu Başlatıldı!")
        await client.start()

asyncio.run(start_revolt_bot())