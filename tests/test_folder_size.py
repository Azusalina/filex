"""Recursive contents totals and asynchronous q-panel updates in a real terminal."""
import os
from pathlib import Path
import tempfile
import unittest
from filex.details import metadata
from test_runtime_fixes import ROOT, Terminal


class FolderSizeTests(unittest.TestCase):
    def test_nested_hidden_excluded_links_and_refresh(self):
        with tempfile.TemporaryDirectory(prefix='filex-folder-total-') as d:
            base = Path(d)
            root = base/'data'; root.mkdir()
            (root/'sub').mkdir(); (root/'.hidden').mkdir(); (root/'empty').mkdir()
            (root/'a').write_bytes(b'123')
            (root/'sub/b').write_bytes(b'12345')
            (root/'.hidden/c').write_bytes(b'1234567')
            os.link(root/'a', root/'hardlink')
            (root/'cycle').symlink_to(root, target_is_directory=True)
            os.mkfifo(root/'fifo')
            config = base/'settings.conf'
            config.write_text('[input_method]\nauto_english=false\n[terminal]\nmode="tty"\ncharset="ascii"\n[browser]\nexcluded_paths=['+repr(str(root/'.hidden'))+']\n')
            self.assertEqual(metadata(root)['size_bytes'], 18)
            t = Terminal([str(ROOT/'filex.sh'),str(root),'--config',str(config)],root)
            self.addCleanup(t.close)
            t.until(lambda:b'Space:mark' in t.output)
            t.send('q')
            # No extra key is sent: the completed background scan must repaint itself.
            t.until(lambda:b'18 bytes (4 files)' in t.output)
            self.assertNotIn(b'Directory metadata size',t.output)
            (root/'sub/b').write_bytes(b'123456')
            t.output.clear();t.send('\x12')
            t.until(lambda:b'19 bytes (4 files)' in t.output)
            t.send('\x06empty\r');t.send('\x1b')
            t.until(lambda:b'0 bytes (0 files)' in t.output)
            t.send('Q');self.assertEqual(t.process.wait(timeout=5),0)
