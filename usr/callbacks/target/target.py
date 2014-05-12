#!/usr/bin/env python
# encoding: utf-8

import urllib2
import json
import pickle
import glob
import httplib
import os
import threading
import errno
from datetime import datetime
from lib.command.Command import UserInput
from util.Res import Res
from util import Util
from lib.sound import Sound
from util.log import *
from lib.model import Callback


class target_callback(Callback.Callback):
    def callback(self,
            action=None,
            target=None,
            msg=None, 
            pre_value=None):
        INFO("* target callback: %s, message: %s pre_value: %s" %(target, msg, pre_value))
        return True, "pass"


class weather_report_callback(Callback.Callback):
    def callback(self, cmd, action, target, msg, pre_value):
        url = 'http://m.weather.com.cn/data/101280101.html'  # Guangzhou
        re = urllib2.urlopen(url).read()
        re = re.decode('UTF-8')
        we = json.loads(re)['weatherinfo']

        info = ""
        info += u'城市：' + we['city'] + "\n"
        info += u'日期：' + we['date_y'] + "\n"
        info += u'week：' + we['week'] + "\n"
        info += u'未来6天天气：' + "\n"
        info += '\t' + we['temp1'] + '\t' + we['weather1'] + '\t' + we['wind1'] + "\n"
        info += '\t' + we['temp2'] + '\t' + we['weather2'] + '\t' + we['wind2'] + "\n"
        info += '\t' + we['temp3'] + '\t' + we['weather3'] + '\t' + we['wind3'] + "\n"
        info += '\t' + we['temp4'] + '\t' + we['weather4'] + '\t' + we['wind4'] + "\n"
        info += '\t' + we['temp5'] + '\t' + we['weather5'] + '\t' + we['wind5'] + "\n"
        info += '\t' + we['temp6'] + '\t' + we['weather6'] + '\t' + we['wind6'] + "\n"
        info += u'穿衣指数: ' + we['index_d'] + "\n"
        info += u'紫外线: ' + we['index_uv']

        self._home.publish_msg(cmd, info)

        content = ""
        if msg == u"明天":
            content += u'明天天气：' + ',' + we['temp2'] + ',' + we['weather2'] + '.\n'
        elif msg == u"今天":
            content += u'今天天气：' + ',' + we['temp1'] + ',' + we['weather1'] + '.\n'
        else:
            content += u'今天天气：' + ',' + we['temp1'] + ',' + we['weather1'] + '.\n'
            content += u'明天天气：' + ',' + we['temp2'] + ',' + we['weather2'] + '.\n'
            content += u'后天天气：' + ',' + we['temp3'] + ',' + we['weather3'] + '.\n'
        content += u'穿衣指数：' + we['index_d'] + '\n'

        self._speaker.speak(content.split('\n'))

        return True, True


class douban_callback(Callback.Callback):

    __music_table = {
        "华语":"1",
        "欧美":"2",
        "70":"3",
        "80":"4",
        "90":"5",
        "粤语":"6",
        "摇滚":"7",
        "民谣":"8",
        "轻音乐":"9",
        "电影原声":"10",
        "爵士":"13",
        "电子":"14",
        "说唱":"15",
        "R&B":"16",
        "日语":"17",
        "韩语":"18",
        "女声":"20",
        "特仑苏":"21",
        "法语":"22",
        "豆瓣音乐人":"26",
                }
    
    def callback(self,
            action=None,
            target = None,
            msg = None, 
            pre_value = None):
        if pre_value == "play":
            music_id = "9" # 轻音乐
            if msg in self.__music_table:
                music_id = self.__music_table[msg]
            play = self._context["player"] 
            httpConnection = httplib.HTTPConnection('douban.fm')
            httpConnection.request('GET', '/j/mine/playlist?type=n&channel=' + music_id)
            song = json.loads(httpConnection.getresponse().read())['song']
            play(song[0]['url'], inqueue=False)
        return True, "pass"

class message_callback(Callback.Callback):
    def callback(
            self,
            action=None,
            target=None,
            msg=None, 
            pre_value=None):
        if pre_value == "new":
            path = "usr/message/"
            try:
                os.makedirs(path)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(path):
                    pass
                else:
                    ERROR(exc)
                    return False

            self._home.setResume(True)
            filepath = path + datetime.now().strftime("%m-%d_%H:%M") + ".mp3"
            record = self._context["recorder"]
            record(filepath)
            Sound.play(
                        Res.get_res_path("sound/com_stop")
                        )
            self._home.setResume(False)
        elif pre_value == "play":
            self._home.setResume(True)

            play = self._context["player"]
            for idx, filepath in enumerate(glob.glob("usr/message/*.mp3")):
                self._speaker.speak(u'第%d条留言' % (idx + 1))
                play(filepath)

            Sound.play(
                        Res.get_res_path("sound/com_stop")
                        )

            self._home.setResume(False)
        elif pre_value == "remove":
            filelist = glob.glob("usr/message/*.mp3")
            for f in filelist:
                os.remove(f)
                INFO("remove:%s" % (f, ))
            Sound.play(
                        Res.get_res_path("sound/com_trash")
                        )
        return True, "pass"


class record_callback(Callback.Callback):
    def callback(self,
            action=None,
            target=None,
            msg=None, 
            pre_value=None):
        
        if pre_value == "new":
            path = "usr/memo/"
            try:
                os.makedirs(path)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(path):
                    pass
                else:
                    ERROR(exc)
                    return False

            self._home.setResume(True)
            filepath = path + datetime.now().strftime("%m-%d_%H:%M") + ".mp3"
            record = self._context["recorder"]
            record(filepath)
            Sound.play(
                        Res.get_res_path("sound/com_stop")
                        )
            self._home.setResume(False)
        return True


class bell_callback(Callback.Callback):
    def callback(self,
            action=None,
            target=None,
            msg=None, 
            pre_value=None):
        if pre_value == "play":
            if msg is None or not msg.endswith(u"次"):
                count = 5
            else:
                count = int(Util.cn2dig(msg[:-1]))
            self._home.setResume(True)
            url = Sound.get_play_request_url(
                                            Res.get_res_path("sound/com_bell")
                                            , loop=count)
            play = self._context["player"]
            play(url)
            self._home.setResume(False)
        return True


class todo_callback(Callback.Callback):

    todo_path = "todo.pcl"

    def __init__(self):
        super(todo_callback, self).__init__()
        self._lock = threading.Lock()
        self.load_todos()

    def load_todos(self):
        self.todos = []
        with self._lock:
            try:
                with open(todo_callback.todo_path, "rb") as f:
                    self.todos = pickle.load(f)
            except:
                INFO("empty todo list.")
        return self.todos

    def save_todos(self):
        with self._lock:
            try:
                with open(todo_callback.todo_path, "wb") as f:
                    pickle.dump(self.todos, f, True)
            except Exception, e:
                ERROR(e)
                ERROR("invaild save todo path:%s", self.todo_path)

    def todo_at_index(self, index):
        if index < 0 or index >= len(self.todos):
            ERROR("invaild todo index.")
            return NULL
        else:
            return self.todos[index]

    def add_todo(self, content):
        if content is None or len(content) == 0:
            ERROR("empty ecript content.")
            return False
        self.todos.append(content)
        return True

    def remove_todo_at_index(self, index):
        if index < 0 or index >= len(self.todos):
            ERROR("invaild todo index.")
            return False
        else:
            del self.todos[index]
            self.save_todos()
            return True

    def callback(self, cmd, action, target, msg, pre_value):
        if pre_value == "show":
            info = ""
            self.load_todos()
            for index, todo in enumerate(self.todos):
                info += u"序号: %d\n    内容:%s\n"  \
                        % (index, self.todos[index])
            if len(info) == 0:
                info = u"当前无" + target
            else:
                info = info[:-1]
            self._home.publish_msg(cmd, info)
        elif pre_value == "new":
            if Util.empty_str(msg):
                cancel_flag = u"取消"
                finish_flag = u"完成"
                self._home.publish_msg(
                    cmd
                    , u"请输入内容, 输入\"%s\"或\"%s\"结束:" % (finish_flag, cancel_flag)
                    , cmd_type="input"
                )
                msg = UserInput(self._home).waitForInput(
                                                        finish=finish_flag,
                                                        cancel=cancel_flag)
            if msg is None  \
                    or not self.add_todo(msg):
                self._home.publish_msg(cmd, u"新建失败")
            else:
                self._home.publish_msg(cmd, u"新建成功")
                self.save_todos()
        elif pre_value == "remove":
            index = Util.cn2dig(msg)
            if not index is None:
                if self.remove_todo_at_index(int(index)):
                    INFO("remove todo: " + msg)
                    self._home.publish_msg(cmd
                            , u"删除" + target + ": " + msg)
                else:
                    self._home.publish_msg(cmd, u"删除失败")
            else:
                self._home.publish_msg(cmd, u"删除失败")
        return True


class task_callback(Callback.Callback):
    def callback(self, cmd, action, msg, pre_value):
        if pre_value == "show":
            threads = self._home._cmd.threads
            info = u""
            if len(threads) <= 1: #  当前任务不计入
                info += u"当前无任务"
                INFO(info)
                self._home.publish_msg(cmd, info)
            else:
                info += u"任务列表:"
                for thread_index in threads:
                    if threads[thread_index][0] == cmd:
                        continue
                    info += u"\n  序号：%d 内容：%s" % (thread_index, threads[thread_index][0])
                INFO(info)
                self._home.publish_msg(cmd, info)
        elif pre_value == "break":
            thread_index = Util.cn2dig(msg)
            if thread_index is None or thread_index == '':
                WARN("invaild thread index %s" % (thread_index, ))
                return False, None
            else:
                thread_index = int(thread_index)
            if thread_index in self._home._cmd.threads:
                cmd, thread = self._home._cmd.threads[thread_index]
                thread.stop()
                self._home.publish_msg(cmd, u"停止执行任务%d" % (thread_index, ))
                INFO("stop thread: %d with cmd: %s" % (thread_index, cmd))
        return True, True


class script_callback(Callback.Callback):

    script_path = "scripts.pcl"

    def __init__(self):
        super(script_callback, self).__init__()
        self._lock = threading.Lock()
        self.load_scripts()

    def load_scripts(self):
        self.scripts = {}
        with self._lock:
            try:
                with open(script_callback.script_path, "rb") as f:
                    self.scripts = pickle.load(f)
            except:
                INFO("empty script list.")
        return self.scripts

    def save_scripts(self):
        with self._lock:
            try:
                with open(script_callback.script_path, "wb") as f:
                    pickle.dump(self.scripts, f, True)
            except Exception, e:
                ERROR(e)
                ERROR("invaild save script path:%s", self.script_path)

    def script_by_name(self, name):
        if name in self.scripts:
            return self.scripts[name]
        return None

    def add_script(self, name, content):
        if name is None or len(name) == 0:
            ERROR("empty script name.")
            return False
        if content is None or len(content) == 0:
            ERROR("empty ecript content.")
            return False
        self.scripts[name] = content
        return True

    def remove_script_by_name(self, name):
        if name in self.scripts:
            del self.scripts[name]
            self.save_scripts()
            return True
        return False

    def run_script(self, name):
        script = self.script_by_name(name)
        if script is None or len(script) == 0:
            ERROR("empty script content or invaild script name.")
            return
        else:
            self._home.parse_cmd(script)

    def callback(self, cmd, action, msg, pre_value):
        if pre_value == "show":
            info = ""
            self.load_scripts()
            for script_name in self.scripts:
                info += u"名称: " + script_name  \
                        + u"\n    内容: " + self.scripts[script_name]  \
                        + "\n"
            if len(info) == 0:
                info = u"当前无" + target
            else:
                info = info[:-1]
            self._home.publish_msg(cmd, info)
            INFO(info)
        else:
            if msg is None or len(msg) == 0:
                self._home.publish_msg(cmd, u"缺少脚本名称")
                return False
            script_name = msg
            if pre_value == "new":
                cancel_flag = u"取消"
                finish_flag = u"完成"
                self._home.publish_msg(cmd
                        , u"脚本名称: " + script_name  \
                        + u"\n请输入脚本内容, 输入\"" + cancel_flag  \
                        + u"\"或\"" + finish_flag + u"\"结束..."
                        , cmd_type="input")
                userinput = UserInput(self._home).waitForInput(
                                                            finish=finish_flag,
                                                            cancel=cancel_flag)
                if userinput is None  \
                        or not self.add_script(script_name, userinput):
                    self._home.publish_msg(cmd, u"新建脚本失败")
                else:
                    self._home.publish_msg(cmd, u"成功新建脚本")
                    self.save_scripts()
            elif pre_value == "remove":
                if self.remove_script_by_name(script_name):
                    INFO("remove script: " + script_name)
                    self._home.publish_msg(cmd, u"删除脚本:" + script_name)
            elif pre_value == "run":
                self._home.publish_msg(cmd, u"执行脚本:" + script_name)
                self.run_script(script_name)
        return True


class switch_callback(Callback.Callback):
    def callback(self, cmd, action, target, msg, pre_value):
        if pre_value == "show":
            if msg == u"列表" or msg == u"状态":
                states = self._home._switch.list_state()
                if states is None:
                    self._home.publish_msg(cmd, u"内部错误")
                elif len(states) == 0:
                    self._home.publish_msg(cmd, target + u"列表为空")
                else:
                    info = target + u"列表:"
                    for switch_ip in states:
                        switch_name = self._home._switch.name_for_ip(switch_ip)
                        info += u"\n  名称:" \
                                + switch_name \
                                + u" 状态:" \
                                + states[switch_ip]["state"]
                    self._home.publish_msg(cmd, info)
        return True


class lamp_callback(Callback.Callback):
    def callback(self, cmd, action, target, msg, pre_value):
        ip = self._home._switch.ip_for_name(target)
        if pre_value == "on":
            return True
        elif pre_value == "off":
            return True
        elif pre_value == "show" and msg == u"状态":
            state = self._home._switch.show_state(ip)
            if state is None:
                self._home.publish_msg(cmd, u"内部错误")
                return False
            info = u"名称:" \
                   + target \
                   + u" 状态:" \
                   + state
            self._home.publish_msg(cmd, info)
            return True, state
        else:
            return False


class speech_callback(Callback.Callback):
    def callback(self, cmd, action, target, msg, pre_value):
        if pre_value == "play":
            if Util.empty_str(msg):
                cancel_flag = u"取消"
                finish_flag = u"完成"
                self._home.publish_msg(cmd
                        , u"请输入内容, 输入\"" + cancel_flag  \
                        + u"\"或\"" + finish_flag + u"\"结束..."
                        , cmd_type="input")
                userinput = UserInput(self._home).waitForInput(
                                                            finish=finish_flag,
                                                            cancel=cancel_flag)
                if userinput is None:
                    WARN("speech content is None.")
                    self._home.publish_msg(cmd, u"语音内容为空")
                    return True
                else:
                    self._speaker.speak(userinput)
            else:
                self._speaker.speak(msg)
        return True
