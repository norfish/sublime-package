#  -*- coding:utf-8 -*-
import os
import json
import sublime, sublime_plugin

try:
    import commands
except Exception as e:
    import subprocess

class QunarSync():
    item_list = []
    local_path = None
    remote_path = '/'
    sync_type = 'all'

    def run(self, command_object, edit, sync_type, file = None):
        self.view = command_object.view
        config_file = self.find_config(file)['file_path']
        if (config_file is False) :
            return
        if (config_file is None) :
            sublime.error_message('can not find config(qsync-conf.json) file')
            return

        if (sync_type is 'file'):
            self.remote_path = self.find_remote_path(file)
            self.sync_type = 'file'

        self.start(config_file)

    def find_remote_path(self, file):
        filePath = file or self.view.file_name()
        config_file = self.find_config(file)['folder_path']
        return filePath.replace(config_file, '')


    def find_config(self, file):
        filePath = file or self.view.file_name()
        ret = {'file_path': None}

        if (filePath is None) :
            sublime.error_message('no file be opend')
            return False

        nowPath = os.path.split(filePath)[0]
        while os.path.split(nowPath)[1] is not '':
            config_path = os.path.join(nowPath, 'qsync-conf.json')
            if (os.path.exists(config_path) is True):
                ret = {'folder_path':nowPath, 'file_path':config_path}
                self.local_path = nowPath + ''
                return ret
            else:
                nowPath = (os.path.split(nowPath))[0]
        return ret

    def start(self, config_file):
        fp = open(config_file, 'r')
        try:
            data = json.load(fp)
        except Exception as e:
            sublime.error_message('qsync-conf.json is no a json file')
            return
        self.analysis_conf(data)

    def analysis_conf(self, data):
        keys = []
        self.item_list = []
        for k in data:
            item = data[k]
            try:
                host = item["host"]
                path = item["path"]
            except Exception as e:
                sublime.error_message('qsync-conf.json can\'t be format,there is no host or path')
                return
            keys.append(k)
            self.item_list.append(item)
        if(len(keys) == 1):
            self.on_get_item_index(0)
        else:
            #keys.reverse()
            #self.item_list.reverse()
            self.show_panel(keys)

    def show_panel(self, keys):
        self.view.window().show_quick_panel(keys, self.on_get_item_index)

    def on_get_item_index(self, index):
        if(index < 0):
            return;
        item = self.item_list[index]
        host = item["host"]
        path = item["path"]
        if (sublime.ok_cancel_dialog('sync\n"%s"\nto\n"%s:%s"' %(self.local_path + self.remote_path, host, path + self.remote_path)) is not True):
            return
        self.do_sync(item)

    def do_sync(self, item):
        self.view.window().run_command('show_panel', {"panel": "console", "reverse":True})
        host = item["host"]
        path = item["path"] + self.remote_path
        exclude = ['.svn']
        include = []
        local_path = self.local_path + self.remote_path
        sync_type = self.sync_type
        other_args = sync_type is not 'file'

        user = self.get(item, "user")
        if (user is not None):
            user = user + '@'
        else:
            user = ''

        if (self.get(item, "exclude") is not None and other_args):
            ex = self.get(item, "exclude")
            for it in ex.split(' '):
                exclude.append(it)

        for i in range(0, len(exclude)):
            exclude[i] = "--exclude=" + exclude[i]

        exclude = ' '.join(exclude)

        if (self.get(item, "include") is not None and other_args):
            ex = self.get(item, "include")
            for it in ex.split(' '):
                include.append(it)

        for i in range(0, len(include)):
            include[i] = "--include=" + include[i]

        include = ' '.join(include)

        del_conf = self.get(item, "del")
        isdel = '--del'
        if (del_conf is False and other_args):
            isdel = ''

        sync_command = 'rsync -rzcv %s --timeout=10 --chmod="a=rX,u+w" --rsync-path="sudo rsync" %s %s %s %s%s:%s ' %(isdel, include, exclude, local_path, user, host, path)
        print(sync_command)
        try:
            status, output = commands.getstatusoutput(sync_command)
        except Exception as e:
            status, output = subprocess.getstatusoutput(sync_command)
        print(output)
        return

    def get(self, data, key):
        try:
            return data[key]
        except Exception as e:
            return None

class QunarSyncCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        qunarSync = QunarSync()
        qunarSync.run(self, edit, 'all')

class QunarSyncThisFileCommand(sublime_plugin.TextCommand):
    def run(self, edit, paths = []):
        qunarSync = QunarSync()
        paths_len = len(paths)

        if (paths_len > 0):
            for item in paths:
                qunarSync.run(self, edit, 'file', item)
        else:        
            qunarSync.run(self, edit, 'file')