"""Creation modifiers travel through an attached tmux client, not send-keys."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid
from test_runtime_fixes import ROOT, Terminal


@unittest.skipUnless(shutil.which('tmux'), 'requires tmux')
class TmuxCreationTests(unittest.TestCase):
    def test_real_client_creation_sequences(self):
        with tempfile.TemporaryDirectory(prefix='filex-tmux-creation-') as d:
            root = Path(d)
            config = root/'.config.conf'
            config.write_text('[input_method]\nauto_english=false\n')
            socket = 'filex-creation-'+uuid.uuid4().hex
            def tmux(*args):
                return subprocess.run(['tmux', '-L', socket, *args], text=True,
                                      capture_output=True, check=True).stdout.strip()
            self.addCleanup(lambda: subprocess.run(['tmux','-L',socket,'kill-server'],capture_output=True))
            terminal = Terminal(['tmux','-L',socket,'-f','/dev/null','new-session','-s','fixture',
                                 str(ROOT/'filex.sh'),str(root),'--config',str(config)],root)
            self.addCleanup(terminal.close)
            terminal.until(lambda: b'Space:mark' in terminal.output)
            for sequence, name, folder in [
                ('\x0e', 'plain.txt', False),
                ('\x1b[27;6;78~', 'konsole-folder', True),
                ('\x1b[110;6u', 'csi-folder', True),
                ('\x1b\x0e', 'alt-folder', True),
                ('\x1b[110;7u', 'alt-csi-folder', True),
                ('\x1b[14;3u', 'control-codepoint-folder', True),
                ('\x1b[14;2u', 'shift-control-codepoint-folder', True),
            ]:
                with self.subTest(sequence=repr(sequence)):
                    terminal.send(sequence)
                    terminal.send(name+'\r')
                    terminal.until(lambda:(root/name).exists())
                    self.assertEqual((root/name).is_dir(),folder)
                    tmux('send-keys','Left')
            terminal.send('Q')

    def test_direct_shifted_codepoint_keeps_directory_action(self):
        # tmux 3.8 does not accept Kitty alternate-key syntax on its client side;
        # crossterm accepts it when a supporting terminal connects directly.
        with tempfile.TemporaryDirectory(prefix='filex-shifted-creation-') as d:
            root = Path(d)
            config = root/'.config.conf'
            config.write_text('[input_method]\nauto_english=false\n')
            terminal = Terminal([str(ROOT/'filex.sh'),str(root),'--config',str(config)],root)
            self.addCleanup(terminal.close)
            terminal.until(lambda:b'Space:mark' in terminal.output)
            terminal.send('\x1b[110:78;6u')
            terminal.send('shifted-folder\r')
            terminal.until(lambda:(root/'shifted-folder').exists())
            self.assertTrue((root/'shifted-folder').is_dir())
            terminal.send('Q')
