import json, re, shutil, subprocess, threading, urllib.parse, urllib.request
from datetime import datetime

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.app import App

try:
    from jnius import autoclass
    ANDROID = True
except Exception:
    ANDROID = False

PINK = (1, 0.2, 0.6, 1)
DARK = (0.09, 0.09, 0.11, 1)
USER = "AFAQ"
HAS_TERMUX = shutil.which("termux-tts-speak") is not None
Window.clearcolor = (0, 0, 0, 1)


def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def http_get(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "KHUSHBO/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def speak(text):
    if HAS_TERMUX:
        subprocess.Popen(["termux-tts-speak", text[:500]])
    else:
        try:
            from plyer import tts
            tts.speak(text[:500])
        except Exception:
            pass


def listen():
    if HAS_TERMUX:
        return run(["termux-speech-to-text"], timeout=30)
    return ""


def android_open_package(pkg):
    if not ANDROID:
        return False
    try:
        act = autoclass("org.kivy.android.PythonActivity").mActivity
        intent = act.getPackageManager().getLaunchIntentForPackage(pkg)
        if intent is None:
            return False
        act.startActivity(intent)
        return True
    except Exception:
        return False


def open_app(pkg, url=None):
    if android_open_package(pkg):
        return True
    if HAS_TERMUX:
        if url:
            run(["termux-open-url", url])
        else:
            run(["monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])
        return True
    return False


def torch(on):
    if HAS_TERMUX:
        run(["termux-torch", "on" if on else "off"])
        return True
    try:
        from plyer import flash
        flash.on() if on else flash.off()
        return True
    except Exception:
        return False


def battery():
    if HAS_TERMUX:
        try:
            return json.loads(run(["termux-battery-status"]))["percentage"]
        except Exception:
            return None
    try:
        from plyer import battery as b
        return int(b.status["percentage"])
    except Exception:
        return None


def call_number(num):
    if HAS_TERMUX:
        run(["termux-telephony-call", num])
        return True
    if ANDROID:
        try:
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            act = autoclass("org.kivy.android.PythonActivity").mActivity
            i = Intent(Intent.ACTION_CALL, Uri.parse("tel:" + num))
            act.startActivity(i)
            return True
        except Exception:
            return False
    return False


def weather():
    try:
        return http_get("https://wttr.in/Lahore?format=3").strip()
    except Exception:
        return "Mausam ka data nahi mil saka."


def wikipedia(q):
    try:
        s = json.loads(http_get(
            "https://en.wikipedia.org/w/api.php?action=opensearch&limit=1&format=json&search="
            + urllib.parse.quote(q)))
        if not s[1]:
            return None
        t = urllib.parse.quote(s[1][0].replace(" ", "_"))
        d = json.loads(http_get("https://en.wikipedia.org/api/rest_v1/page/summary/" + t))
        return d.get("extract")
    except Exception:
        return None


def duckduckgo(q):
    try:
        d = json.loads(http_get(
            "https://api.duckduckgo.com/?format=json&no_html=1&skip_disambig=1&q="
            + urllib.parse.quote(q)))
        return d.get("AbstractText") or d.get("Answer") or (
            d["RelatedTopics"][0]["Text"] if d.get("RelatedTopics") else None)
    except Exception:
        return None


def internet_answer(q):
    clean = re.sub(r"\b(matlab|kya hai|kya hota hai|kaun hai|batao|bataye|what is|who is|meaning)\b",
                   "", q, flags=re.I).strip() or q
    return wikipedia(clean) or duckduckgo(q) or duckduckgo(clean) or \
        "Maaf kijiye AFAQ, is ka jawab nahi mila."


def process(cmd):
    c = cmd.lower().strip()
    if any(k in c for k in ("torch on", "torch chalu", "torch jalao", "torch kholo")):
        return "Torch on kar di AFAQ." if torch(True) else "Torch on nahi ho saki."
    if any(k in c for k in ("torch off", "torch band", "torch bujhao")):
        return "Torch band kar di AFAQ." if torch(False) else "Torch off nahi ho saki."
    if "youtube" in c:
        open_app("com.google.android.youtube", "https://youtube.com")
        return "YouTube khol raha hoon AFAQ."
    if "whatsapp" in c:
        open_app("com.whatsapp", "https://wa.me/")
        return "WhatsApp khol raha hoon AFAQ."
    if "tiktok" in c:
        open_app("com.zhiliaoapp.musically", "https://tiktok.com") or \
            open_app("com.ss.android.ugc.trill", "https://tiktok.com")
        return "TikTok khol raha hoon AFAQ."
    if "camera" in c:
        ok = open_app("com.android.camera") or open_app("com.google.android.GoogleCamera") \
            or open_app("com.sec.android.app.camera")
        return "Camera khol diya AFAQ." if ok else "Camera nahi khul saka."
    if "time" in c or "waqt" in c or "samay" in c:
        return "AFAQ, abhi waqt hai " + datetime.now().strftime("%I:%M %p")
    if "battery" in c:
        b = battery()
        return f"AFAQ, battery {b} percent hai." if b is not None else "Battery ka pata nahi chala."
    if "call" in c:
        num = re.sub(r"[^\d+]", "", c.replace(" ", ""))
        if len(num) < 5:
            return "Number batayen, jaise: call karo 03001234567"
        return f"{num} ko call kar raha hoon." if call_number(num) else "Call nahi lag saki."
    if "mausam" in c or "weather" in c:
        return weather()
    return internet_answer(cmd)


class RoundMic(ButtonBehavior, Widget):
    dy = NumericProperty(0)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self.draw, size=self.draw, dy=self.draw)
        self.anim = None
        self.draw()

    def draw(self, *a):
        self.canvas.clear()
        with self.canvas:
            Color(1, 0.2, 0.6, 0.25)
            Ellipse(pos=(self.x - dp(10), self.y + self.dy - dp(10)),
                    size=(self.width + dp(20), self.height + dp(20)))
            Color(*PINK)
            Ellipse(pos=(self.x, self.y + self.dy), size=self.size)
            Color(0, 0, 0, 1)
            Ellipse(pos=(self.center_x - dp(8), self.y + self.dy + self.height * 0.4),
                    size=(dp(16), dp(34)))

    def start_anim(self):
        self.anim = (Animation(dy=dp(18), d=.35) + Animation(dy=-dp(18), d=.35))
        self.anim.repeat = True
        self.anim.start(self)

    def stop_anim(self):
        if self.anim:
            self.anim.cancel(self)
        Animation(dy=0, d=.15).start(self)


class Khushbo(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(8), **kw)
        self.add_widget(Label(text="KHUSHBO", font_size=sp(46), bold=True, color=PINK,
                              size_hint_y=None, height=dp(70)))
        area = FloatLayout(size_hint_y=.32)
        self.mic = RoundMic(size_hint=(None, None), size=(dp(120), dp(120)),
                            pos_hint={"center_x": .5, "center_y": .5})
        self.mic.bind(on_release=lambda *a: self.voice())
        area.add_widget(self.mic)
        self.add_widget(area)

        self.chat = Label(text="", markup=True, size_hint_y=None, halign="left",
                          valign="top", color=(1, 1, 1, 1), font_size=sp(16))
        self.chat.bind(width=lambda w, v: setattr(w, "text_size", (v, None)),
                       texture_size=lambda w, s: setattr(w, "height", s[1] + dp(10)))
        self.scroll = ScrollView()
        self.scroll.add_widget(self.chat)
        self.add_widget(self.scroll)

        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        self.inp = TextInput(multiline=False, hint_text="Yahan likhein...",
                             background_color=DARK, foreground_color=(1, 1, 1, 1),
                             cursor_color=PINK, hint_text_color=(.6, .6, .6, 1))
        self.inp.bind(on_text_validate=lambda *a: self.send())
        row.add_widget(self.inp)
        row.add_widget(Button(text="BHEJO", size_hint_x=None, width=dp(80), bold=True,
                              background_normal="", background_color=PINK,
                              on_release=lambda *a: self.send()))
        row.add_widget(Button(text="MIC BOLO", size_hint_x=None, width=dp(100), bold=True,
                              background_normal="", background_color=(.25, .25, .3, 1),
                              on_release=lambda *a: self.voice()))
        self.add_widget(row)
        Clock.schedule_once(lambda dt: self.reply(f"Ji {USER}, hukum karein"), .5)

    def add(self, who, text):
        col = "ff3399" if who == "KHUSHBO" else "ffffff"
        self.chat.text += f"[b][color={col}]{who}:[/color][/b] {text}\n\n"
        Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), .1)

    def reply(self, text, say=True):
        self.add("KHUSHBO", text)
        if say:
            speak(text)

    def send(self):
        t = self.inp.text.strip()
        if not t:
            return
        self.inp.text = ""
        self.add(USER, t)
        threading.Thread(target=self.work, args=(t, False), daemon=True).start()

    def voice(self):
        self.mic.start_anim()
        self.add("KHUSHBO", "Sun rahi hoon...")
        threading.Thread(target=self.listen_work, daemon=True).start()

    def listen_work(self):
        text = listen()
        Clock.schedule_once(lambda dt: self.mic.stop_anim())
        if not text:
            Clock.schedule_once(lambda dt: self.reply(
                f"{USER}, awaz samajh nahi aayi. Dobara bolein.", False))
            return
        Clock.schedule_once(lambda dt: self.add(USER, text))
        self.work(text, True)

    def work(self, text, by_voice):
        ans = process(text)
        Clock.schedule_once(lambda dt: self.reply(ans, True))


class KhushboApp(App):
    title = "KHUSHBO"

    def build(self):
        if ANDROID:
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.CAMERA, Permission.CALL_PHONE,
                                     Permission.RECORD_AUDIO])
            except Exception:
                pass
        return Khushbo()


if __name__ == "__main__":
    KhushboApp().run()
