"""Inherited filename patterns across a subtree, exact overrides, and CLI rendering."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from filex.config import load_config
from filex.core import Browser
from test_runtime_fixes import ROOT


class RecursiveOrderTests(unittest.TestCase):
    def test_config_and_cli_inherit_extension_order_without_touching_other_trees(self):
        with tempfile.TemporaryDirectory(prefix='filex-recursive-order-') as d:
            base = Path(d)
            site = base/'site'
            nested = site/'nested'
            deep = nested/'deep'
            outside = base/'site-other'
            for directory in [site, nested, deep, outside]:
                directory.mkdir(parents=True, exist_ok=True)
                for name in ['a.js', 'm.css', 'z.html']:
                    (directory/name).touch()
            config = base/'settings.conf'
            config.write_text(f"[recursive_order.'{site}']\nsequence=['%.html','%.css','%.js','%']\n")
            for directory in [site, nested, deep]:
                with self.subTest(directory=directory):
                    browser = Browser(directory, load_config(config))
                    self.assertEqual([n.path.name for n in browser.root.children[:3]],
                                     ['z.html', 'm.css', 'a.js'])
                    output = self.tree(directory, config)
                    self.assertLess(output.index('z.html'), output.index('m.css'))
                    self.assertLess(output.index('m.css'), output.index('a.js'))
            output = self.tree(outside, config)
            self.assertLess(output.index('a.js'), output.index('z.html'))
            # A directory override affects only itself, retaining recursive rules below it.
            config.write_text(config.read_text() + f"\n[directory_order.'{nested}']\nsequence=['=a.js','%']\n")
            output = self.tree(nested, config)
            self.assertLess(output.index('a.js'), output.index('z.html'))
            output = self.tree(deep, config)
            self.assertLess(output.index('z.html'), output.index('a.js'))

    def tree(self, directory, config):
        return subprocess.run([str(ROOT/'filex.sh'), str(directory), '--config', str(config),
                               '--print-tree', '--ascii'], capture_output=True, text=True,
                              check=True).stdout

    def test_recursive_rule_requires_an_absolute_path(self):
        with tempfile.TemporaryDirectory() as d:
            config = Path(d)/'settings.conf'
            config.write_text("[recursive_order.site]\nsequence=['%.html']\n")
            with self.assertRaisesRegex(ValueError, 'absolute'):
                load_config(config)
