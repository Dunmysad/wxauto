# main.py
import tkinter as tk
from tkinter import ttk, messagebox
from uiautomation import WindowControl
import re
import json
import os

class WX:
    def __init__(self):
        self.wx = WindowControl(Name="微信")
        self.wx.SwitchToThisWindow()

    def get_message(self):
        return self.wx.ListControl(Name="消息").GetChildren()[-1].Name.replace("\n", "")

    def process_message(self, ms, conditions):
        # 检查是否以@所有人开头
        if not ms.strip().startswith("@所有人"):
            return True
            
        # 根据UI设置的条件进行判断
        contains_forbidden_words = any(word in ms for word in conditions['forbidden_words'])
        match_pattern = re.search(r'扣\s*(.*?)\s*接单', ms) if conditions['use_pattern'] else None
        
        if not contains_forbidden_words and not match_pattern:
            self.wx.SendKeys('1{ENTER}')
            return False
        elif match_pattern:
            self.wx.SendKeys(match_pattern.group(1) + '{ENTER}')
            return False
        else:
            return True

class WXAutoUI:
    def __init__(self, root):
        self.root = root
        self.root.title("微信自动回复设置")
        self.root.geometry("500x400")
        
        # 从JSON文件加载配置
        self.load_config()
        
        self.setup_ui()
        
    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.conditions = {
                    'forbidden_words': config.get('forbidden_words', ["大师", "钻", "分", "段", "猎"]),
                    'use_pattern': config.get('use_pattern', True)
                }
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果配置文件不存在或格式错误，使用默认值
            self.conditions = {
                'forbidden_words': ["大师", "钻", "分", "段", "猎"],
                'use_pattern': True
            }
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 禁用关键词设置
        keywords_frame = ttk.LabelFrame(main_frame, text="禁用关键词（勾选后包含对应词时不自动回复）", padding="5")
        keywords_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2, padx=2)
        
        # 创建预设关键词的复选框
        self.forbidden_word_vars = {}
        checkboxes_frame = ttk.Frame(keywords_frame)
        checkboxes_frame.pack(fill=tk.X, expand=True)
        
        # 从配置加载关键词并创建复选框
        for word in self.conditions['forbidden_words']:
            var = tk.BooleanVar(value=word in self.conditions['forbidden_words'])
            checkbox = ttk.Checkbutton(
                checkboxes_frame,
                text=word,
                variable=var
            )
            checkbox.pack(side=tk.LEFT, padx=1, pady=1, ipadx=2, ipady=2)
            self.forbidden_word_vars[word] = var
        
        # 正则表达式模式设置
        pattern_frame = ttk.LabelFrame(main_frame, text="正则表达式匹配", padding="10")
        pattern_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.use_pattern_var = tk.BooleanVar(value=self.conditions['use_pattern'])
        pattern_check = ttk.Checkbutton(
            pattern_frame, 
            text="启用 '扣XX接单' 模式匹配并自动回复括号内内容",
            variable=self.use_pattern_var
        )
        pattern_check.grid(row=0, column=0, sticky=tk.W)
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="开始监控", command=self.start_monitoring)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="停止监控", command=self.stop_monitoring, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="运行状态", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_var = tk.StringVar(value="未运行")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0)
        
        # 配置列权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        pattern_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(0, weight=1)
        
        self.wx_instance = None
        self.monitoring = False
        
    def update_conditions(self):
        # 更新条件设置
        # 获取被勾选的禁用词
        selected_words = [word for word, var in self.forbidden_word_vars.items() if var.get()]
        self.conditions['forbidden_words'] = selected_words
        self.conditions['use_pattern'] = self.use_pattern_var.get()
        
    def start_monitoring(self):
        try:
            self.wx_instance = WX()
            self.monitoring = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_var.set("正在监控...")
            self.root.after(1000, self.monitor_loop)
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {str(e)}")
            
    def stop_monitoring(self):
        self.monitoring = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_var.set("已停止")
        
    def monitor_loop(self):
        if not self.monitoring:
            return
            
        try:
            self.update_conditions()
            message = self.wx_instance.get_message()
            continue_monitoring = self.wx_instance.process_message(message, self.conditions)
            
            if not continue_monitoring:
                self.stop_monitoring()
                self.status_var.set("已发送回复，监控停止")
                return
                
        except Exception as e:
            self.status_var.set(f"错误: {str(e)}")
            
        if self.monitoring:
            self.root.after(1000, self.monitor_loop)

if __name__ == '__main__':
    root = tk.Tk()
    app = WXAutoUI(root)
    root.mainloop()
