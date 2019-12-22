import re
import subprocess

import sublime
import sublime_plugin

ANSI_ESCAPE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

settings = None


def plugin_loaded():
    global settings
    settings = sublime.load_settings('shfmt.sublime-settings')


class Formatter(object):

  def __init__(self, view):
    self.view = view
    self.window = view.window()
    self.encoding = view.encoding()

    if self.encoding == 'Undefined':
        self.encoding = 'utf-8'
    self.cmd = settings.get('cmd', ['shfmt', ' -sr -i 2 -ci', '-'])

  def format(self, region):
    contents = self.view.substr(region)
    # run the formatting tool
    output, error = self._exec(contents)
    if error:
        self._show_errors(error)
        return contents
    self._hide_errors()
    return output

  def _exec(self, stdin):
    proc = subprocess.Popen(
      self.cmd,
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE
    )

    stdout, stderr = proc.communicate(stdin.encode())
    if stderr or proc.returncode != 0:
      return "", stderr.decode('utf-8')
    else:
      return stdout.decode(self.encoding), None

  def _show_errors(self, errors):
    panel = self.window.create_output_panel('shfmt')
    panel.set_scratch(True)
    panel.run_command('select_all')
    panel.run_command('right_delete')
    panel.run_command('insert', {'characters': ANSI_ESCAPE.sub('', errors)})
    self.window.run_command('show_panel', {'panel': 'output.shfmt'})

  def _hide_errors(self):
    self.window.run_command('hide_panel', {'panel': 'output.shfmt'})


class shfmtCommand(sublime_plugin.TextCommand):
  def is_enabled(self):
    return self.view.score_selector(0, 'source.bash') != 0

  def run(self, edit):
    formatter = Formatter(self.view)
    region = sublime.Region(0, self.view.size())
    replacement = formatter.format(region)

    if self.view.substr(region) != replacement:
      self.view.replace(edit, region, replacement)


class shfmtListener(sublime_plugin.EventListener):
  def on_pre_save(self, view):

    if settings.get('format_on_save', True):
      view.run_command('shfmt')
