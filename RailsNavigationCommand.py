import sublime, sublime_plugin
import re
import sys
import os
import glob

clean_name = re.compile('^\s*(public\s+|private\s+|protected\s+|static\s+|function\s+|def\s+)+', re.I)

class RailsNavigation(sublime_plugin.WindowCommand):
    def is_view(self, view):
        file_name = view.file_name()

        for extension in sublime.load_settings('RailsNavigation.sublime-settings').get('view_extensions'):
            if file_name.endswith('.' + extension):
                return True

    def is_controller(self, view):
        file_name = view.file_name()
        return len(view.file_name().split('app/controllers/')) > 1

    def show_action(self, view):
        action_name     = self.action_name(view)
        project_dir     = view.file_name().split('app/views')[0]
        controller_path = os.path.join(project_dir, 'app/controllers', self.controller_name(view))
        new_view        = self.window.open_file(controller_path)

        self.scroll_to_action(new_view, action_name)

    def scroll_to_action(self, view, action_name):
        if view.is_loading():
            sublime.set_timeout(lambda: self.scroll_to_action(view, action_name), 50)
            return
        else:
            function_regions = view.find_by_selector('meta.function - meta.function.inline')
            if function_regions:
                for r in reversed(function_regions):
                    line = view.substr(r)
                    if re.search(r'def +%s' % action_name, line):
                        view.show(r)
                        view.sel().clear()
                        view.sel().add(sublime.Region(r.b, r.b))
                        break


    def action_name(self, view):
        return os.path.basename(view.file_name()).split('.')[0]

    def controller_name(self, view):
        view_path = view.file_name().split('app/views/')[1]
        return os.path.dirname(view_path) + '_controller.rb'

    def method_name(self, view):
      name = None

      for region in view.sel():
          region_row, region_col = view.rowcol(region.begin())

          function_regions = view.find_by_selector('meta.function - meta.function.inline')
          if function_regions:
              for r in reversed(function_regions):
                  row, col = view.rowcol(r.begin())
                  if row <= region_row:
                      lines = view.substr(r).splitlines()
                      name  = clean_name.sub('', lines[0]).split('(')[0].split(':')[0].strip()
                      break
      return name

    def open_view(self, view):
        method_name = self.method_name(view)
        if not method_name:
            return

        self.path = []
        for extension in sublime.load_settings('RailsNavigation.sublime-settings').get("view_extensions"):
            view_glob = view.file_name().replace('/app/controllers/', '/app/views/').replace('_controller.rb', '/') + method_name + '*' + '.' + extension
            print(view_glob)
            self.path.extend(glob.glob(view_glob))

        self.path = list(set(self.path))

        if len(self.path) == 1:
            self.window.open_file(self.path[0])
        if len(self.path) > 1:
            minfied_path = list(map(lambda p: p.split('app/views/')[1], self.path))
            view.show_popup_menu(minfied_path, self.action)

    def action(self, payload):
        self.window.open_file(self.path[payload])

    def run(self):
        view = self.window.active_view()

        if self.is_view(view):
            self.show_action(view)
        if self.is_controller(view):
            self.open_view(view)
