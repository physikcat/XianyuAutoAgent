import tkinter as tk
from tkinter import ttk
import sys
from io import StringIO
from hello import Hello

class ParameterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("参数输入界面")
        
        # 输入框框架
        input_frame = ttk.LabelFrame(root, text="输入参数", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 创建3个输入框
        self.entries = []
        for i in range(3):
            ttk.Label(input_frame, text=f"参数{i+1}:").grid(row=i, column=0, sticky=tk.W)
            entry = ttk.Entry(input_frame)
            entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=2)
            self.entries.append(entry)
            
        # 输出框框架
        output_frame = ttk.LabelFrame(root, text="输出结果", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建输出文本框
        self.output_text = tk.Text(output_frame, height=10)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 运行按钮
        run_button = ttk.Button(root, text="运行", command=self.run_program)
        run_button.pack(pady=10)
        
    def run_program(self):
        # 获取输入参数
        params = [entry.get() for entry in self.entries]
        
        # 重定向标准输出
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        try:
            # 创建Hello实例并运行
            hello = Hello(*params)
            hello.run()
            
            # 恢复标准输出并获取结果
            sys.stdout = old_stdout
            output = mystdout.getvalue()
            
            # 显示结果
            self.output_text.insert(tk.END, f"输入参数: {params}\n")
            self.output_text.insert(tk.END, output)
            self.output_text.see(tk.END)
        except Exception as e:
            sys.stdout = old_stdout
            self.output_text.insert(tk.END, f"错误: {str(e)}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ParameterGUI(root)
    root.mainloop()
