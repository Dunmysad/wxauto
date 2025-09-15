from uiautomation import WindowControl
import re


class WX:
    def __init__(self):
        self.wx = WindowControl(Name="微信")
        self.wx.SwitchToThisWindow()

    def get_message(self):
        return self.wx.ListControl(Name="消息").GetChildren()[-1].Name.replace("\n", "")

    def process_message(self, ms):
        if ms.strip().startswith("@所有人") and \
                "大师" not in ms and \
                "钻" not in ms and \
                "分" not in ms and \
                "段" not in ms and \
                not re.search(r'扣\s*(.*?)\s*接单', ms):
            self.wx.SendKeys('1{ENTER}')
            return False
        elif ms.strip().startswith("@所有人") and re.search(r'扣\s*(.*?)\s*接单', ms):
            self.wx.SendKeys(re.findall(r'扣\s*(.*?)\s*接单', ms)[0] + '{ENTER}')
            return False
        else:
            return True


if __name__ == '__main__':
    wx_instance = WX()
    loop = True
    while loop:
        message = wx_instance.get_message()
        loop = wx_instance.process_message(message)