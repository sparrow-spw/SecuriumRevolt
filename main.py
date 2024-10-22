import os
import json
import asyncio
import revolt
import aiohttp
from typing import Union
from revolt.ext import commands
import time
import datetime

def load_json_data(dosya_adi):
    if os.path.exists(dosya_adi):
        with open(dosya_adi, 'r') as f:
            return json.load(f)
    return {}

def save_json_data(dosya_adi, veri):
    with open(dosya_adi, 'w') as f:
        json.dump(veri, f, indent=4)

class Client(commands.CommandsClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baslangic_zamani = time.monotonic()

    async def get_prefix(self, mesaj: revolt.Message):
        return "s!"

    async def on_ready(self):
        sunucular = self.servers 
        sunucu_sayisi = len(sunucular)
        await self.edit_status(presence=revolt.PresenceType.online, text=f"{sunucu_sayisi} sunucuda")
        print(f"Revolt botu {sunucu_sayisi} sunucuda çalışıyor.")
        
    async def on_member_join(self, uye: revolt.Member):
        sunucu_id = str(uye.server.id)
        veritabanı = load_json_data('database.json')
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

            embed = revolt.SendableEmbed(
                title="🏓 Pong!",
                description=f"Gecikme süresi *{ping}*ms",
                colour="#00FF00"
            )

            await msg.edit(content=None, embeds=[embed])

        elif mesaj.content.startswith("s!kick"):
            izinler = mesaj.author.get_permissions()
            if izinler.kick_members:
                args = mesaj.content.split()
                if len(args) > 1:
                    kullanici_id = args[1].strip("<@!>")
                    kullanici = mesaj.server.get_member(kullanici_id)
                    if kullanici:
                        await kullanici.kick()
                        embed = revolt.SendableEmbed(
                            title="✅ Kullanıcı Atıldı",
                            description=f"**{kullanici.name}** başarıyla atıldı.",
                            colour="#FF0000"
                        )
                        await mesaj.channel.send(embeds=[embed])
                    else:
                        await mesaj.channel.send("❌ Kullanıcı bulunamadı.")
                else:
                    await mesaj.channel.send("❌ Lütfen bir kullanıcı ID'si belirtin.")
            else:
                await mesaj.channel.send("❌ Bu komutu kullanmak için yeterli yetkiniz yok.")

        elif mesaj.content.startswith("s!ban"):
            izinler = mesaj.author.get_permissions()
            if izinler.ban_members:
                args = mesaj.content.split()
                if len(args) > 1:
                    kullanici_id = args[1].strip("<@!>")
                    kullanici = mesaj.server.get_member(kullanici_id)
                    if kullanici:
                        await kullanici.ban()
                        embed = revolt.SendableEmbed(
                            title="🔨 Kullanıcı Yasaklandı",
                            description=f"**{kullanici.name}** başarıyla yasaklandı.",
                            colour="#FF0000"
                        )
                        await mesaj.channel.send(embeds=[embed])
                    else:
                        await mesaj.channel.send("❌ Kullanıcı bulunamadı.")
                else:
                    await mesaj.channel.send("❌ Lütfen bir kullanıcı ID'si belirtin.")
            else:
                await mesaj.channel.send("❌ Bu komutu kullanmak için yeterli yetkiniz yok.")

        elif mesaj.content.startswith("s!avatar"):
            args = mesaj.content.split()
            if len(args) > 1:
                kullanici_id = args[1].strip("<@!>")
                kullanici = mesaj.server.get_member(kullanici_id)
            else:
                kullanici = mesaj.author

            if kullanici:
                embed = revolt.SendableEmbed(
                    title=f"{kullanici.name} adlı kullanıcının avatarı",
                    description="",
                    colour="#3498db"
                )
                await mesaj.channel.send(embeds=[embed])
                await mesaj.channel.send(kullanici.avatar.url)
            else:
                await mesaj.channel.send("❌ Kullanıcı bulunamadı.")

        elif mesaj.content.startswith("s!durum"):
            surum = "1.0.1"
            sunucu_sayisi = len(self.servers)
            toplam_uyeler = sum(len(server.members) for server in self.servers)
            calisma_suresi = time.monotonic() - self.baslangic_zamani
            calisma_saniye = int(calisma_suresi)
            calisma_mesaji = f"{calisma_saniye // 3600} saat, {(calisma_saniye % 3600) // 60} dakika, {calisma_saniye % 60} saniye"

            embed = revolt.SendableEmbed(
                title="🤖 Bot Durumu",
                description=(
                    f"📦 **Sürüm:** {surum}\n"
                    f"🌐 **Sunucu Sayısı:** {sunucu_sayisi}\n"
                    f"👥 **Toplam Üye Sayısı:** {toplam_uyeler}\n"
                    f"⏳ **Çalışma Süresi:** {calisma_mesaji}\n"
                ),
                colour="#00FF00"
            )
            await mesaj.channel.send(embeds=[embed])

        elif mesaj.content.startswith("s!help") or mesaj.content == self.user.mention:
            komutlar_listesi = {
                "🔧 **Temel Komutlar:**": [
                    ("s!ping", "Botun çalıştığını kontrol eder."),
                    ("s!durum", "Botun durumu hakkında bilgi verir."),
                    ("s!avatar <@kullanıcı>", "Belirtilen kullanıcının avatarını gösterir."),
                    ("s!kullanıcı <@kullanıcı>", "Belirtilen kullanıcı hakkında bilgi verir."),
                    ("s!random", "1 ile 100 arasında rastgele bir sayı üretir."),
                    ("s!yazıtura", "Yazı veya tura atar."),
                    ("s!quote", "Rastgele bir alıntı gösterir."),
                    ("s!matematik <işlem>", "Belirtilen matematik işlemini hesaplar."),
                    ("s!sunucu", "Sunucu hakkında bilgi verir."),
                ],
                "👮 **Yönetim Komutları:**": [
                    ("s!kick <kullanici id>", "Belirtilen kullanıcıyı sunucudan atar."),
                    ("s!ban <kullanici id>", "Belirtilen kullanıcıyı sunucudan yasaklar."),
                ],
                " **Otomasyon Komutları:**": [
                    ("s!otorol <rol id>", "Yeni üyelere otomatik rol verir."),
                    ("s!herkeserolver <rol id>", "Tüm üyelere belirtilen rolü verir."),
                ],
                "🌐 **Sunucu Bilgisi:**": [
                    ("s!sunucu", "Sunucu hakkında bilgi verir."),
                ],
            }
            
            guncelleme_notlari = (
                "🆕 **Güncelleme Notları (1.0.2):**\n"
                "- `s!random`, `s!yazıtura`, `s!quote`, `s!matematik` ve `s!sunucu` komutları artık embedli.\n"
                "- Yardım menüsüne yeni komutlar eklendi.\n"
            )

            yardim_mesaji = "📜 **Komutlar:**\n"
            for kategori, komutlar in komutlar_listesi.items():
                yardim_mesaji += f"{kategori}\n"
                for komut, aciklama in komutlar:
                    yardim_mesaji += f"  - **{komut}**: {aciklama}\n"
                yardim_mesaji += "\n"

            yardim_mesaji += guncelleme_notlari

            embed = revolt.SendableEmbed(
                title="Yardım Menüsü",
                description=yardim_mesaji,
                colour="#0000FF"
            )

            await mesaj.channel.send(embeds=[embed])

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

        elif mesaj.content.startswith("s!kullanıcı"):
            args = mesaj.content.split()
            if len(args) > 1:
                kullanici_id = args[1].strip("<@!>")
                kullanici = mesaj.server.get_member(kullanici_id)
            else:
                kullanici = mesaj.author

            if kullanici:
                roller = ", ".join([rol.name for rol in kullanici.roles]) if kullanici.roles else "Yok"
                olusturulma_tarihi = kullanici.created_at.strftime('%Y-%m-%d %H:%M:%S')
                katilma_tarihi = kullanici.joined_at.strftime('%Y-%m-%d %H:%M:%S')
                
                simdi = datetime.datetime.now(datetime.timezone.utc)
                hesap_olusturma_suresi = simdi - kullanici.created_at
                olusturma_yillar = hesap_olusturma_suresi.days // 365
                olusturma_aylar = (hesap_olusturma_suresi.days % 365) // 30
                olusturma_gunler = (hesap_olusturma_suresi.days % 365) % 30

                sunucuya_katilma_suresi = simdi - kullanici.joined_at
                katilma_yillar = sunucuya_katilma_suresi.days // 365
                katilma_aylar = (sunucuya_katilma_suresi.days % 365) // 30
                katilma_gunler = (sunucuya_katilma_suresi.days % 365) % 30

                embed = revolt.SendableEmbed(
                    title=f"{kullanici.name} Kullanıcı Bilgisi",
                    description=(
                        f"**ID:** {kullanici.id}\n"
                        f"**Ad:** {kullanici.name}\n"
                        f"**Durum:** {kullanici.status}\n"
                        f"**Oluşturulma Tarihi:** {olusturulma_tarihi} *({olusturma_yillar} yıl, {olusturma_aylar} ay, {olusturma_gunler} gün önce)*\n"
                        f"**Sunucuya Katılma Tarihi:** {katilma_tarihi} *({katilma_yillar} yıl, {katilma_aylar} ay, {katilma_gunler} gün önce)*\n"
                        f"**Roller:** {roller}\n"
                    ),
                    colour="#3498db",
                    thumbnail=kullanici.avatar.url
                )
                
                await mesaj.channel.send(embeds=[embed])
            else:
                await mesaj.channel.send("❌ Kullanıcı bulunamadı.")

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
                    veritabanı = load_json_data('database.json')
                    otorol_verisi = veritabanı.get('otorol', {})
                    otorol_verisi[str(mesaj.server.id)] = rol_id
                    veritabanı['otorol'] = otorol_verisi
                    save_json_data('database.json', veritabanı)
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

        elif mesaj.content.startswith("s!random"):
            import random
            rastgele_sayi = random.randint(1, 100)
            embed = revolt.SendableEmbed(
                title="🎲 Rastgele Sayı",
                description=f"**Sonuç:** {rastgele_sayi}",
                colour="#FFA500"
            )
            await mesaj.channel.send(embeds=[embed])

        elif mesaj.content.startswith("s!yazıtura"):
            import random
            sonuc = random.choice(["Yazı", "Tura"])
            embed = revolt.SendableEmbed(
                title="🪙 Yazı Tura",
                description=f"**Sonuç:** {sonuc}",
                colour="#FFD700"
            )
            await mesaj.channel.send(embeds=[embed])

        elif mesaj.content.startswith("s!quote"):
            quotes = [
                "Hayat, bisiklet sürmek gibidir. Dengede kalmak için hareket etmelisiniz. - Albert Einstein",
                "Başarı, genellikle başarısızlıkla sonuçlanan hataların toplamıdır. - Thomas Edison",
                "Kendine inan. Her şeyin mümkün olduğunu bil. - Audrey Hepburn"
            ]
            import random
            alinti = random.choice(quotes)
            embed = revolt.SendableEmbed(
                title="📜 Alıntı",
                description=alinti,
                colour="#8A2BE2"
            )
            await mesaj.channel.send(embeds=[embed])

        elif mesaj.content.startswith("s!matematik"):
            args = mesaj.content.split(" ", 1)
            if len(args) > 1:
                try:
                    sonuc = eval(args[1], {"__builtins__": None}, {})
                    embed = revolt.SendableEmbed(
                        title="🧮 Matematik Sonucu",
                        description=f"**Sonuç:** {sonuc}",
                        colour="#00FF7F"
                    )
                    await mesaj.channel.send(embeds=[embed])
                except Exception as e:
                    await mesaj.channel.send("❌ Geçersiz matematik işlemi.")
            else:
                await mesaj.channel.send("❌ Lütfen bir matematik işlemi belirtin.")

        elif mesaj.content.startswith("s!sunucu"):
            sunucu_adi = mesaj.server.name
            sunucu_sahibi = mesaj.server.owner.name
            uye_sayisi = len(mesaj.server.members)
            çevrimiçi_uyeler = sum(1 for uye in mesaj.server.members if uye.status == revolt.PresenceType.online)
            rol_sayisi = len(mesaj.server.roles)
            olusma_tarihi = mesaj.server.created_at.strftime("%Y-%m-%d %H:%M:%S")

            embed = revolt.SendableEmbed(
                title="🌐 Sunucu Bilgileri",
                description=(
                    f"🏷️ **Sunucu Adı:** {sunucu_adi}\n"
                    f"👤 **Sahibi:** {sunucu_sahibi}\n"
                    f"👥 **Toplam Üye Sayısı:** {uye_sayisi}\n"
                    f"🟢 **Çevrimiçi Üye Sayısı:** {çevrimiçi_uyeler}\n"
                    f"🎭 **Rol Sayısı:** {rol_sayisi}\n"
                    f"📅 **Oluşturulma Tarihi:** {olusma_tarihi}\n"
                ),
                colour="#FFA500"
            )
            await mesaj.channel.send(embeds=[embed])

async def start_revolt_bot():
    while True:
        try:
            async with revolt.utils.client_session() as session:
                client = Client(session, os.getenv("REVOLT_TOKEN"))
                print("Revolt Securium Botu Başlatıldı!")
                await client.start()
        except Exception as e:
            print(f"Bot bir hata nedeniyle durdu: {e}")
            print("Bot yeniden başlatılıyor...")
            await asyncio.sleep(5)

asyncio.run(start_revolt_bot())
