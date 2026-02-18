import base64
import aiohttp
import asyncio
import random
from pyaxmlparser import APK
from src.config import settings


class SecurityAnalyzer:

    # --- 1. APK TAHLILI (CPU-intensive) ---
    @staticmethod
    def analyze_apk(file_path):
        """
        APK faylni tahlil qiladi.
        """
        try:
            try:
                apk = APK(file_path)
            except Exception:
                return "❌ Fayl tuzilishi buzilgan yoki shifrlangan."

            if not apk.package:
                return "⚠️ Paket nomini aniqlab bo'lmadi (Obfuscated APK)."

            perms = apk.get_permissions() or []

            # Tahlil jarayoni
            risk_score, risk_details = SecurityAnalyzer._calculate_risk_score(perms)
            patterns = SecurityAnalyzer._detect_threat_patterns(perms)

            app_name = apk.get_app_name() or "Noma'lum"
            version = apk.version_name or "1.0"
            package = apk.package

            ai_commentary = SecurityAnalyzer._generate_human_message(
                app_name, risk_score, patterns, risk_details, is_url=False
            )

            color_bar, _ = SecurityAnalyzer._get_visuals(risk_score)

            report = (
                f"📦 **Ilova:** {app_name}\n"
                f"🆔 **Paket:** `{package}`\n"
                f"v{version}\n"
                f"➖➖➖➖➖➖➖➖➖➖\n"
                f"🛡 **Xavfsizlik:** {100 - risk_score}%\n"
                f"📊 **Xavf:** {color_bar} ({risk_score}/100)\n\n"
                f"{ai_commentary}\n"
            )
            return report

        except Exception as e:
            return f"❌ Tahlilda xatolik: {str(e)[:100]}"

    # --- 2. HAVOLA (URL) TAHLILI (Smart Scan) ---
    @staticmethod
    async def analyze_url(url):
        """
        VirusTotal API orqali havolani tekshiradi.
        Agar havola yangi bo'lsa, uni majburan skanerlashga yuboradi.
        """
        if not settings.VT_API_KEY:
            return "⚠️ VirusTotal API kaliti sozlanmagan (.env faylni tekshiring)."

        headers = {"x-apikey": settings.VT_API_KEY}

        try:
            # 1-QADAM: URL ID yasash
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
            api_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"

            async with aiohttp.ClientSession() as session:
                # 2-QADAM: Bazadan tekshirib ko'ramiz
                async with session.get(api_url, headers=headers) as response:

                    # Agar 404 bo'lsa, demak bu YANGI LINK. Uni skanerlashga yuboramiz.
                    if response.status == 404:
                        scan_url = "https://www.virustotal.com/api/v3/urls"
                        async with session.post(scan_url, headers=headers, data={"url": url}) as scan_res:
                            if scan_res.status != 200:
                                return f"❌ Skanerlash xatosi: {scan_res.status}"

                            # Skanerlashga yuborildi, lekin natija darhol chiqmaydi.
                            # Foydalanuvchini kutirmaslik uchun "Dastlabki tahlil" beramiz.
                            return (
                                f"ℹ️ **Yangi Havola Aniqlandi!**\n\n"
                                f"Men ushbu havolani (`{url}`) global antivirus bazasiga yubordim.\n"
                                f"Tahlil endi boshlandi. Hozircha bu havola noma'lum, shuning uchun **kirishni tavsiya etmayman**."
                            )

                    elif response.status != 200:
                        return f"❌ API Xatosi: {response.status}"

                    # Agar 200 bo'lsa (Bazada bor), natijani olamiz
                    data = await response.json()
                    attributes = data.get("data", {}).get("attributes", {})

                    stats = attributes.get("last_analysis_stats", {})
                    malicious = stats.get("malicious", 0)
                    suspicious = stats.get("suspicious", 0)

                    # AI Logikasi: Havola kategoriyasi (masalan: fishing, malware)
                    categories = attributes.get("categories", {})
                    category_text = ", ".join(list(categories.values())[:2]) if categories else "Umumiy"

                    risk_score = min((malicious + suspicious) * 20, 100)

                    patterns = []
                    if malicious > 0: patterns.append(f"🚫 {malicious} ta antivirus blokladi.")
                    if suspicious > 0: patterns.append(f"⚠️ {suspicious} ta antivirus shubhali dedi.")

                    ai_commentary = SecurityAnalyzer._generate_human_message(
                        "Ushbu Havola", risk_score, patterns, [], is_url=True
                    )

                    color_bar, _ = SecurityAnalyzer._get_visuals(risk_score)

                    report = (
                        f"🌐 **Havola:** `{url}`\n"
                        f"📂 **Turi:** {category_text}\n"
                        f"➖➖➖➖➖➖➖➖➖➖\n"
                        f"🛡 **Xavfsizlik:** {100 - risk_score}%\n"
                        f"📊 **Xavf:** {color_bar} ({risk_score}/100)\n\n"
                        f"{ai_commentary}\n"
                    )
                    return report

        except Exception as e:
            return f"❌ Havolani tekshirishda xatolik: {str(e)}"

    # --- YORDAMCHI FUNKSIYALAR ---

    @staticmethod
    def _calculate_risk_score(perms):
        score = 0
        details = []
        weights = {
            "SEND_SMS": (30, "SMS yuborish"),
            "RECEIVE_SMS": (30, "SMS o'qish"),
            "CAMERA": (20, "Kamera"),
            "RECORD_AUDIO": (20, "Mikrofon"),
            "READ_CONTACTS": (15, "Kontaktlar"),
            "ACCESS_FINE_LOCATION": (10, "Joylashuv"),
            "SYSTEM_ALERT_WINDOW": (15, "Oyna ustidan chiqish"),
            "INSTALL_PACKAGES": (20, "Ilova o'rnatish"),
        }

        for key, (weight, desc) in weights.items():
            for p in perms:
                if key in p:
                    score += weight
                    details.append(desc)
                    break
        return min(score, 100), details

    @staticmethod
    def _detect_threat_patterns(perms):
        patterns = []
        p_str = " ".join(perms)

        if "RECORD_AUDIO" in p_str and "INTERNET" in p_str:
            patterns.append("🎙️ **Ovozli josuslik** (Mikrofon + Internet)")
        if "CAMERA" in p_str and "INTERNET" in p_str:
            patterns.append("📸 **Kamera josusligi** (Kamera + Internet)")
        if "SMS" in p_str and "INTERNET" in p_str:
            patterns.append("💳 **SMS O'g'risi** (SMS + Internet)")
        if "INSTALL_PACKAGES" in p_str:
            patterns.append("📲 **Troyan Dropper** (Boshqa viruslarni o'rnatishi mumkin)")

        return patterns

    @staticmethod
    def _get_visuals(score):
        if score < 20:
            return "🟢" * (score // 10) + "⚪" * (10 - (score // 10)), "✅"
        elif score < 50:
            return "🟡" * (score // 10) + "⚪" * (10 - (score // 10)), "⚠️"
        return "🔴" * (score // 10) + "⚪" * (10 - (score // 10)), "⛔"

    @staticmethod
    def _generate_human_message(name, score, patterns, details, is_url=False):
        # AI Muloqot uslubi (NLG)
        if is_url:
            if score == 0:
                msg = [
                    f"✅ **Xavfsiz Sayt.**\nGlobal xavfsizlik bazalarida bu havola toza deb belgilangan.",
                    f"👍 **Yaxshi natija.**\nBu saytda hozircha hech qanday tahdid aniqlanmadi."
                ]
                return random.choice(msg)
            elif score > 50:
                return f"⛔ **O'TA XAVFLI!**\nBu havola orqali KIRMANG! U fishing (soxta sayt) yoki virus yuklovchi manba bo'lishi mumkin."
            else:
                return f"⚠️ **Ehtiyotkorlik talab etiladi.**\nBu sayt ba'zi antiviruslar tomonidan shubhali deb topilgan."

        # APK uchun
        if score < 15:
            return f"✅ **Xavfsiz Ilova.**\n`{name}` ilovasida zararli kodlar alomatlari topilmadi."
        elif score < 50:
            reasons = ", ".join(details[:3])
            return f"⚠️ **Shubhali Harakatlar.**\nBu ilova **{reasons}** ruxsatlarini so'ramoqda. Agar bu uning vazifasi bo'lmasa, o'rnatmang."
        else:
            pat_text = "\n".join([f"❗ {p}" for p in patterns])
            return f"⛔ **HAVF DARAJASI: YUQORI!**\nBiz bu faylda virus xususiyatlarini aniqladik:\n\n{pat_text}\n\n🗑 **Qat'iy tavsiya:** O'chirib tashlang."